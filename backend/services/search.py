"""
Search service for executing Elasticsearch queries.
Handles multi-algorithm search execution, error handling, and response mapping.
"""

import time
from typing import Dict, Any, List, Optional
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError, BadRequestError
from models.search import (
    SearchRequest,
    Bm25IdNameSearchRequest,
    SearchResponse,
    GameResult,
    GameIdName,
    Bm25IdNameSearchResponse,
    MultiAlgorithmSearchResponse,
    AlgorithmResult,
    RankedResult,
)
from services.embedding_service import EmbeddingService
from services.reranker_service import RerankerService
from services.query_builder import QueryBuilder
from services.retrieval_metrics import compute_retrieval_metrics
from config import config
from services.qrels_generation import graded_qrels_for_query, normalized_query_key


class SearchService:
    """
    Service for executing multi-algorithm and Elasticsearch searches.
    Encapsulates all ES interactions and response handling.
    Provides both BM25 and SVM-based ranking algorithms.
    """

    _embedding_service: Optional[EmbeddingService] = None
    _reranker_service: Optional[RerankerService] = None

    @staticmethod
    def _get_embedding_service() -> EmbeddingService:
        if SearchService._embedding_service is None:
            SearchService._embedding_service = EmbeddingService()
        return SearchService._embedding_service

    @staticmethod
    def _get_reranker_service() -> RerankerService:
        if SearchService._reranker_service is None:
            SearchService._reranker_service = RerankerService()
        return SearchService._reranker_service

    @staticmethod
    def initialize_models() -> None:
        """Pre-load the embedding and reranker models at startup to avoid runtime request latency."""
        es = SearchService._get_embedding_service()
        es._load_model()
        rs = SearchService._get_reranker_service()
        rs._load_model()

    @staticmethod
    def execute_search(
        es_client: Elasticsearch, request: SearchRequest
    ) -> MultiAlgorithmSearchResponse:
        """
        Execute multi-algorithm search (BM25 + SVM).

        Runs both BM25 (Elasticsearch native) and SVM (TF-IDF via Scripted Similarity)
        ranking algorithms against the query and returns results from both.

        Args:
            es_client: Elasticsearch client instance
            request: SearchRequest with query parameters

        Returns:
            MultiAlgorithmSearchResponse with results from both algorithms

        Raises:
            ConnectionError: If ES connection fails
            NotFoundError: If indices don't exist
            BadRequestError: If query is malformed
            ValueError: If response parsing fails
        """
        return SearchService.execute_multi_algorithm_search(
            es_client=es_client, request=request
        )

    @staticmethod
    def execute_bm25_id_name_search(
        es_client: Elasticsearch, request: Bm25IdNameSearchRequest
    ) -> Bm25IdNameSearchResponse:
        """
        Execute BM25 or BM25 hybrid search and return id, name, and platforms per hit.

        Args:
            es_client: Elasticsearch client instance
            request: SearchRequest with query parameters

        Returns:
            Bm25IdNameSearchResponse with slim result rows
        """
        bm25_result = (
            SearchService._execute_bm25_hybrid(es_client=es_client, request=request)
            if request.hybrid
            else SearchService._execute_bm25(es_client=es_client, request=request)
        )
        return SearchService._id_name_response_from_algorithm_result(
            algorithm_result=bm25_result, name_only=request.name_only
        )

    @staticmethod
    def execute_bert_id_name_search(
        es_client: Elasticsearch, request: Bm25IdNameSearchRequest
    ) -> Bm25IdNameSearchResponse:
        """
        Execute BERT semantic search and return id/name results.
        """
        bert_result = SearchService._execute_bert(es_client=es_client, request=request)
        return SearchService._id_name_response_from_algorithm_result(
            algorithm_result=bert_result, name_only=request.name_only
        )

    @staticmethod
    def execute_svm_id_name_search(
        es_client: Elasticsearch, request: Bm25IdNameSearchRequest
    ) -> Bm25IdNameSearchResponse:
        """
        Execute SVM search and return id/name results.
        """
        svm_result = SearchService._execute_svm(es_client=es_client, request=request)
        return SearchService._id_name_response_from_algorithm_result(
            algorithm_result=svm_result, name_only=request.name_only
        )

    @staticmethod
    def _id_name_response_from_algorithm_result(
        algorithm_result: AlgorithmResult, name_only: bool
    ) -> Bm25IdNameSearchResponse:
        return Bm25IdNameSearchResponse(
            results=[
                GameIdName(
                    id=result.id,
                    name=result.name,
                    platforms=None if name_only else result.platforms,
                )
                for result in algorithm_result.results
            ],
            total=algorithm_result.total,
            execution_time_ms=algorithm_result.execution_time_ms,
        )

    @staticmethod
    def execute_multi_algorithm_search(
        es_client: Elasticsearch, request: SearchRequest
    ) -> MultiAlgorithmSearchResponse:
        """
        Execute multi-algorithm search (BM25 + SVM).

        **BM25 Algorithm**: Uses Elasticsearch's native BM25 similarity from games index.
        Multi-match query with field weighting specified in request.

        **SVM Algorithm**: Uses TF-IDF (Vector Space Model) via Scripted Similarity
        from games_svm index. Same query as BM25, but scored with TF-IDF formula:
        score = query.boost × √(freq) × idf × (1/√(length))

        Both algorithms apply the same filters (genres, platforms, etc.).
        Results are returned separately, sorted by score (descending) within each algorithm.

        Args:
            es_client: Elasticsearch client instance
            request: SearchRequest with query text, size, filters, optional explain

        Returns:
            MultiAlgorithmSearchResponse containing:
                - bm25: AlgorithmResult with BM25-ranked results (games index)
                - svm: AlgorithmResult with TF-IDF-ranked results (games_svm index)

        Raises:
            ConnectionError: If ES connection fails
            NotFoundError: If indices don't exist
            BadRequestError: If query is malformed
            ValueError: If response parsing fails
        """
        try:
            # Generate query embedding once to reuse for both hybrid and BERT models
            query_vector = SearchService._get_embedding_service().embed(
                request.query_text
            )

            # Execute BM25 algorithm (from BM25 index)
            bm25_result = SearchService._execute_bm25(
                es_client=es_client, request=request
            )

            # Execute BM25 hybrid algorithm: BM25 base ranking + semantic_embedding matching
            bm25_hybrid_result = SearchService._execute_bm25_hybrid(
                es_client=es_client, request=request, query_vector=query_vector
            )

            # Execute BERT-style semantic embedding search against BM25 index
            bert_result = SearchService._execute_bert(
                es_client=es_client, request=request, query_vector=query_vector
            )

            # Execute SVM algorithm (from SVM index with TF-IDF scripted similarity)
            svm_result = SearchService._execute_svm(
                es_client=es_client, request=request
            )

            # Optionally rerank results with a cross-encoder for all algorithms (batched and deduplicated)
            if getattr(request, "rerank", False):
                # Gather all results and deduplicate by ID, preferring documents with semantic_text
                unique_docs = {}
                for algo_res in [bm25_result, bm25_hybrid_result, bert_result, svm_result]:
                    if algo_res and algo_res.results:
                        for rr in algo_res.results:
                            existing = unique_docs.get(rr.id)
                            if not existing or (not existing.semantic_text and rr.semantic_text):
                                unique_docs[rr.id] = rr

                # Construct unique pairs
                pairs = []
                doc_ids = []
                for doc_id, rr in unique_docs.items():
                    doc_text = rr.semantic_text or f"{rr.name}\n{rr.summary or ''}"
                    pairs.append([request.query_text, doc_text])
                    doc_ids.append(doc_id)

                # Score all unique pairs in a single batch predict call
                if pairs:
                    shared_start = time.time()
                    scores_list = SearchService._get_reranker_service().score_pairs(pairs)
                    shared_inference_time_ms = int((time.time() - shared_start) * 1000)
                    id_to_score = dict(zip(doc_ids, scores_list))
                else:
                    shared_inference_time_ms = 0
                    id_to_score = {}

                # Helper function to map scores back, sort, and update ranks
                def rescore_result(algo_res: AlgorithmResult, label: str) -> AlgorithmResult:
                    if not algo_res or not algo_res.results:
                        return AlgorithmResult(results=[], total=algo_res.total if algo_res else 0, execution_time_ms=0)
                    
                    mapping_start = time.time()
                    
                    scored = []
                    for rr in algo_res.results:
                        score = id_to_score.get(rr.id, 0.0)
                        scored.append((rr, score))
                    
                    scored.sort(key=lambda x: x[1], reverse=True)
                    
                    reranked_results = []
                    for rank, (rr, score) in enumerate(scored, start=1):
                        updated = rr.model_copy(update={
                            "score": float(score),
                            "rank": rank,
                            "algorithm": f"{label}_crossencoder",
                        })
                        reranked_results.append(updated)
                    
                    mapping_time_ms = int((time.time() - mapping_start) * 1000)
                    
                    return AlgorithmResult(
                        results=reranked_results,
                        total=algo_res.total,
                        execution_time_ms=shared_inference_time_ms + mapping_time_ms,
                        explanations=None,
                    )

                bm25_crossencoder_result = rescore_result(bm25_result, "bm25")
                bm25_hybrid_crossencoder_result = rescore_result(bm25_hybrid_result, "bm25_hybrid")
                bert_crossencoder_result = rescore_result(bert_result, "bert")
                svm_crossencoder_result = rescore_result(svm_result, "svm")
            else:
                bm25_crossencoder_result = None
                bm25_hybrid_crossencoder_result = None
                bert_crossencoder_result = None
                svm_crossencoder_result = None

            if request.metrics:
                qid = normalized_query_key(request.query_text)
                grades = graded_qrels_for_query(request.query_text)
                bm25_result = bm25_result.model_copy(
                    update={
                        "metrics": compute_retrieval_metrics(
                            qid, bm25_result.results, grades, request.size
                        ),
                    }
                )
                bm25_hybrid_result = bm25_hybrid_result.model_copy(
                    update={
                        "metrics": compute_retrieval_metrics(
                            qid, bm25_hybrid_result.results, grades, request.size
                        ),
                    }
                )
                bert_result = bert_result.model_copy(
                    update={
                        "metrics": compute_retrieval_metrics(
                            qid, bert_result.results, grades, request.size
                        ),
                    }
                )
                svm_result = svm_result.model_copy(
                    update={
                        "metrics": compute_retrieval_metrics(
                            qid, svm_result.results, grades, request.size
                        ),
                    }
                )

                if getattr(request, "rerank", False):
                    bm25_crossencoder_result = bm25_crossencoder_result.model_copy(
                        update={
                            "metrics": compute_retrieval_metrics(
                                qid, bm25_crossencoder_result.results, grades, request.size
                            ),
                        }
                    )
                    bm25_hybrid_crossencoder_result = bm25_hybrid_crossencoder_result.model_copy(
                        update={
                            "metrics": compute_retrieval_metrics(
                                qid, bm25_hybrid_crossencoder_result.results, grades, request.size
                            ),
                        }
                    )
                    bert_crossencoder_result = bert_crossencoder_result.model_copy(
                        update={
                            "metrics": compute_retrieval_metrics(
                                qid, bert_crossencoder_result.results, grades, request.size
                            ),
                        }
                    )
                    svm_crossencoder_result = svm_crossencoder_result.model_copy(
                        update={
                            "metrics": compute_retrieval_metrics(
                                qid, svm_crossencoder_result.results, grades, request.size
                            ),
                        }
                    )

            return MultiAlgorithmSearchResponse(
                bm25=bm25_result,
                bm25_hybrid=bm25_hybrid_result,
                bert=bert_result,
                svm=svm_result,
                bm25_crossencoder=bm25_crossencoder_result,
                bm25_hybrid_crossencoder=bm25_hybrid_crossencoder_result,
                bert_crossencoder=bert_crossencoder_result,
                svm_crossencoder=svm_crossencoder_result,
            )

        except ConnectionError as e:
            raise ConnectionError(f"Failed to connect to Elasticsearch: {str(e)}")
        except NotFoundError:
            raise NotFoundError(
                f"Indices not found. Ensure both '{config.BM25_INDEX_NAME}' and '{config.SVM_INDEX_NAME}' exist."
            )
        except BadRequestError as e:
            raise BadRequestError(f"Invalid search query: {str(e)}")
        except Exception as e:
            raise ValueError(f"Multi-algorithm search failed: {str(e)}")

    @staticmethod
    def _execute_bm25(
        es_client: Elasticsearch, request: SearchRequest
    ) -> AlgorithmResult:
        """
        Execute BM25 (Elasticsearch native) search.

        Queries the BM25 index (games) using multi_match query with field weights.
        Elasticsearch returns BM25 relevance scores automatically.

        Args:
            es_client: Elasticsearch client instance
            request: SearchRequest with query parameters

        Returns:
            AlgorithmResult with BM25-ranked results
        """
        start_time = time.time()

        try:
            # Build query (same for both algorithms, different index has different similarity)
            query_body = QueryBuilder.build_search_body(request)

            # Execute search against BM25 index
            response = es_client.search(index=config.BM25_INDEX_NAME, body=query_body)
            explanations = (
                SearchService._extract_hit_explanations(response)
                if request.explain
                else None
            )

            # Parse results
            total_count, results_data = SearchService._parse_es_response(response)

            # Convert to RankedResult with BM25 metadata
            ranked_results = [
                SearchService._game_result_to_ranked_result(
                    doc, score, rank + 1, "bm25"
                )
                for rank, (doc, score) in enumerate(results_data)
            ]

            execution_time_ms = int((time.time() - start_time) * 1000)

            return AlgorithmResult(
                results=ranked_results,
                total=total_count,
                execution_time_ms=execution_time_ms,
                explanations=explanations,
            )

        except Exception as e:
            raise ValueError(f"BM25 search failed: {str(e)}")

    @staticmethod
    def _execute_bm25_hybrid(
        es_client: Elasticsearch, request: SearchRequest, query_vector: Optional[List[float]] = None
    ) -> AlgorithmResult:
        """
        Execute BM25 hybrid search.

        Uses the same BM25 base scoring as _execute_bm25, but augments the query
        with a dense vector similarity score from the stored semantic_embedding.
        This preserves the existing BM25 score behavior while adding a semantic
        signal to the hybrid ranking.
        """
        start_time = time.time()

        try:
            if query_vector is None:
                query_vector = SearchService._get_embedding_service().embed(
                    request.query_text
                )
            query_body = QueryBuilder.build_bm25_hybrid_search_body(
                request, query_vector
            )
            response = es_client.search(index=config.BM25_INDEX_NAME, body=query_body)
            explanations = (
                SearchService._extract_hit_explanations(response)
                if request.explain
                else None
            )

            total_count, results_data = SearchService._parse_es_response(response)
            ranked_results = [
                SearchService._game_result_to_ranked_result(
                    doc, score, rank + 1, "bm25_hybrid"
                )
                for rank, (doc, score) in enumerate(results_data)
            ]

            execution_time_ms = int((time.time() - start_time) * 1000)
            return AlgorithmResult(
                results=ranked_results,
                total=total_count,
                execution_time_ms=execution_time_ms,
                explanations=explanations,
            )

        except Exception as e:
            raise ValueError(f"BM25 hybrid search failed: {str(e)}")

    @staticmethod
    def _execute_crossencoder_rerank(
        algorithm_result: AlgorithmResult, query_text: str, algorithm_label: str
    ) -> AlgorithmResult:
        """
        Generic cross-encoder rerank for any AlgorithmResult.

        - Builds (query, document_text) pairs from each RankedResult.
        - Scores with the CrossEncoder
        - Returns a new AlgorithmResult with reranked `results` and updated ranks/scores.
        """
        start_time = time.time()

        original_results = algorithm_result.results
        if not original_results:
            return AlgorithmResult(results=[], total=algorithm_result.total, execution_time_ms=0)

        pairs = []
        for rr in original_results:
            doc_text = rr.semantic_text or f"{rr.name}\n{rr.summary or ''}"
            pairs.append([query_text, doc_text])

        scores = SearchService._get_reranker_service().score_pairs(pairs)

        scored = list(zip(original_results, scores))
        scored.sort(key=lambda x: x[1], reverse=True)

        reranked_results = []
        for new_rank, (orig_rr, score) in enumerate(scored, start=1):
            updated = orig_rr.model_copy(update={
                "score": float(score),
                "rank": new_rank,
                "algorithm": f"{algorithm_label}_crossencoder",
            })
            reranked_results.append(updated)

        execution_time_ms = int((time.time() - start_time) * 1000)

        return AlgorithmResult(
            results=reranked_results,
            total=algorithm_result.total,
            execution_time_ms=execution_time_ms,
        )

    @staticmethod
    def _execute_bert(
        es_client: Elasticsearch, request: SearchRequest, query_vector: Optional[List[float]] = None
    ) -> AlgorithmResult:
        """
        Execute a BERT-style semantic embedding search using BM25 index.

        Searches only the `semantic_embedding` field on the BM25 index, using the
        query embedding and cosine similarity. Filters are applied from the
        request but no lexical text matching is performed.
        """
        start_time = time.time()

        try:
            if query_vector is None:
                query_vector = SearchService._get_embedding_service().embed(
                    request.query_text
                )
            query_body = QueryBuilder.build_bert_search_body(request, query_vector)
            response = es_client.search(index=config.BM25_INDEX_NAME, body=query_body)
            explanations = (
                SearchService._extract_hit_explanations(response)
                if request.explain
                else None
            )

            total_count, results_data = SearchService._parse_es_response(response)
            ranked_results = [
                SearchService._game_result_to_ranked_result(doc, score, rank + 1, "bert")
                for rank, (doc, score) in enumerate(results_data)
            ]

            execution_time_ms = int((time.time() - start_time) * 1000)
            return AlgorithmResult(
                results=ranked_results,
                total=total_count,
                execution_time_ms=execution_time_ms,
                explanations=explanations,
            )

        except Exception as e:
            raise ValueError(f"BERT search failed: {str(e)}")

    @staticmethod
    def _execute_svm(
        es_client: Elasticsearch, request: SearchRequest
    ) -> AlgorithmResult:
        """
        Execute SVM (TF-IDF - Vector Space Model) search.

        Queries the SVM index (games_svm) which uses Scripted Similarity
        to calculate TF-IDF scores. Elasticsearch applies the TF-IDF formula
        directly during query execution, returning TF-IDF scores.

        Formula: score = query.boost × √(freq) × idf × (1/√(length))
        - freq: term frequency in document
        - idf: log((docCount + 1) / (docFreq + 1)) + 1
        - length: number of terms in field

        Args:
            es_client: Elasticsearch client instance
            request: SearchRequest with query parameters

        Returns:
            AlgorithmResult with TF-IDF-ranked results
        """
        start_time = time.time()

        try:
            # Build same query as BM25 - but SVM index uses different similarity
            query_body = QueryBuilder.build_search_body(request)

            # Execute search against SVM index (with scripted TF-IDF similarity)
            response = es_client.search(index=config.SVM_INDEX_NAME, body=query_body)
            explanations = (
                SearchService._extract_hit_explanations(response)
                if request.explain
                else None
            )

            # Parse results - ES already calculated TF-IDF scores
            total_count, results_data = SearchService._parse_es_response(response)

            # Convert to RankedResult with SVM metadata
            ranked_results = [
                SearchService._game_result_to_ranked_result(doc, score, rank + 1, "svm")
                for rank, (doc, score) in enumerate(results_data)
            ]

            execution_time_ms = int((time.time() - start_time) * 1000)

            return AlgorithmResult(
                results=ranked_results,
                total=total_count,
                execution_time_ms=execution_time_ms,
                explanations=explanations,
            )

        except Exception as e:
            raise ValueError(f"SVM search failed: {str(e)}")

    @staticmethod
    def _parse_es_response(es_response: Dict[str, Any]) -> tuple:
        """
        Parse Elasticsearch response and extract documents with ES scores.

        Args:
            es_response: Raw Elasticsearch response dictionary

        Returns:
            Tuple of (total_count, list of (GameResult, score) tuples)

        Raises:
            ValueError: If response structure is invalid
        """
        try:
            # Extract total hits count
            total_hits = es_response.get("hits", {}).get("total", {})

            # Handle both ES 7 and ES 8+ response formats
            if isinstance(total_hits, dict):
                total_count = total_hits.get("value", 0)
            else:
                total_count = total_hits

            # Parse hits with scores
            hits = es_response.get("hits", {}).get("hits", [])
            results_data = [
                (SearchService._parse_hit(hit), float(hit.get("_score", 0.0)))
                for hit in hits
            ]

            return total_count, results_data

        except (KeyError, TypeError) as e:
            raise ValueError(f"Failed to parse Elasticsearch response: {str(e)}")

    @staticmethod
    def _extract_hit_explanations(es_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract explanation payloads from ES hits for API response."""
        hits = es_response.get("hits", {}).get("hits", [])
        return [
            {
                "id": hit.get("_id", ""),
                "score": float(hit.get("_score", 0.0)),
                "explanation": hit.get("_explanation"),
            }
            for hit in hits
        ]

    @staticmethod
    def _parse_response(es_response: Dict[str, Any]) -> SearchResponse:
        """
        Parse Elasticsearch response into SearchResponse model.
        DEPRECATED: Use _parse_es_response for multi-algorithm support.

        Args:
            es_response: Raw Elasticsearch response dictionary

        Returns:
            SearchResponse with parsed results

        Raises:
            ValueError: If response structure is invalid
        """
        try:
            total_count, results_data = SearchService._parse_es_response(es_response)

            # Extract just the GameResult objects
            results = [doc for doc, _ in results_data]

            # Get execution time
            took_ms = es_response.get("took", 0)

            return SearchResponse(results=results, total=total_count, took_ms=took_ms)

        except (KeyError, TypeError) as e:
            raise ValueError(f"Failed to parse Elasticsearch response: {str(e)}")

    @staticmethod
    def _parse_hit(hit: Dict[str, Any]) -> GameResult:
        """
        Convert an Elasticsearch hit into a GameResult model.

        Args:
            hit: Single hit from Elasticsearch response

        Returns:
            GameResult with game data
        """
        source = hit.get("_source", {})

        return GameResult(
            id=source.get("id", hit.get("_id", "")),
            name=source.get("name", ""),
            summary=source.get("summary"),
            category=source.get("category"),
            rating=source.get("rating"),
            aggregated_rating=source.get("aggregated_rating"),
            genres=source.get("genres"),
            themes=source.get("themes"),
            platforms=source.get("platforms"),
            game_modes=source.get("game_modes"),
            player_perspectives=source.get("player_perspectives"),
            keywords=source.get("keywords"),
            release_date=source.get("release_date"),
            cover_url=source.get("cover_url"),
            screenshot_urls=source.get("screenshot_urls"),
            artwork_urls=source.get("artwork_urls"),
            semantic_text=source.get("semantic_text"),
        )

    @staticmethod
    def _game_result_to_ranked_result(
        game: GameResult, es_score: float, rank: int, algorithm: str
    ) -> RankedResult:
        """
        Convert a GameResult to RankedResult with algorithm metadata.

        Args:
            game: GameResult object
            es_score: Elasticsearch relevance score
            rank: Rank position (1-based)
            algorithm: Algorithm name (e.g., "bm25", "svm")

        Returns:
            RankedResult with ranking information
        """
        return RankedResult(
            id=game.id,
            name=game.name,
            summary=game.summary,
            category=game.category,
            rating=game.rating,
            aggregated_rating=game.aggregated_rating,
            genres=game.genres,
            themes=game.themes,
            platforms=game.platforms,
            game_modes=game.game_modes,
            player_perspectives=game.player_perspectives,
            keywords=game.keywords,
            release_date=game.release_date,
            cover_url=game.cover_url,
            screenshot_urls=game.screenshot_urls,
            artwork_urls=game.artwork_urls,
            semantic_text=game.semantic_text,
            score=es_score,
            rank=rank,
            algorithm=algorithm,
        )
