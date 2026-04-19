"""
Search service for executing Elasticsearch queries.
Handles multi-algorithm search execution, error handling, and response mapping.
"""

import time
from typing import Dict, Any
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError, BadRequestError
from models.search import (
    SearchRequest,
    SearchResponse,
    GameResult,
    MultiAlgorithmSearchResponse,
    AlgorithmResult,
    RankedResult,
)
from services.query_builder import QueryBuilder
from config import BM25_INDEX_NAME, SVM_INDEX_NAME


class SearchService:
    """
    Service for executing multi-algorithm and Elasticsearch searches.
    Encapsulates all ES interactions and response handling.
    Provides both BM25 and SVM-based ranking algorithms.
    """

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
            request: SearchRequest with query text, fields, size, filters

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
            # Execute BM25 algorithm (from BM25 index)
            bm25_result = SearchService._execute_bm25(
                es_client=es_client, request=request
            )

            # Execute SVM algorithm (from SVM index with TF-IDF scripted similarity)
            svm_result = SearchService._execute_svm(
                es_client=es_client, request=request
            )

            return MultiAlgorithmSearchResponse(bm25=bm25_result, svm=svm_result)

        except ConnectionError as e:
            raise ConnectionError(f"Failed to connect to Elasticsearch: {str(e)}")
        except NotFoundError:
            raise NotFoundError(
                f"Indices not found. Ensure both '{BM25_INDEX_NAME}' and '{SVM_INDEX_NAME}' exist."
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
            response = es_client.search(index=BM25_INDEX_NAME, body=query_body)

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
            )

        except Exception as e:
            raise ValueError(f"BM25 search failed: {str(e)}")

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
            response = es_client.search(index=SVM_INDEX_NAME, body=query_body)

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
            score=es_score,
            rank=rank,
            algorithm=algorithm,
        )
