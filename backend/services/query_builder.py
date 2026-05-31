"""
Query builder for constructing Elasticsearch queries.
Converts SearchRequest models to Elasticsearch query DSL.
"""

from typing import Dict, Any, List, Optional

from config import DEFAULT_SEARCH_FIELD_WEIGHTS
from models.search import SearchRequest, FilterCriteria


class QueryBuilder:
    """
    Builds Elasticsearch query bodies from search requests.
    Handles multi_match queries with field weighting and filtering.
    """

    @staticmethod
    def build_multi_match_fields() -> List[str]:
        """
        Build multi_match `fields` list from config.DEFAULT_SEARCH_FIELD_WEIGHTS.

        Example:
            [("name", 2), ("summary", 1)] -> ["name^2", "summary"]
        """
        formatted_fields: List[str] = []
        for field, weight in DEFAULT_SEARCH_FIELD_WEIGHTS:
            if weight == 1:
                formatted_fields.append(field)
            else:
                formatted_fields.append(f"{field}^{weight}")
        return formatted_fields

    @staticmethod
    def build_filters(filters: Optional[FilterCriteria]) -> List[Dict[str, Any]]:
        """
        Build Elasticsearch filter clauses from FilterCriteria.
        All filters are ANDed together (must clauses).

        Args:
            filters: FilterCriteria object with optional genres, platforms, etc.

        Returns:
            List of filter dictionaries for Elasticsearch bool query
        """
        if not filters:
            return []

        filter_clauses = []

        # Multi-value filters (any match)
        if filters.genres:
            filter_clauses.append({"terms": {"genres": filters.genres}})

        if filters.game_modes:
            filter_clauses.append({"terms": {"game_modes": filters.game_modes}})

        if filters.platforms:
            filter_clauses.append({"terms": {"platforms": filters.platforms}})

        if filters.player_perspectives:
            filter_clauses.append(
                {"terms": {"player_perspectives": filters.player_perspectives}}
            )

        if filters.themes:
            filter_clauses.append({"terms": {"themes": filters.themes}})

        # Date range filter
        if filters.release_date:
            date_range = {}
            if filters.release_date.start_date:
                date_range["gte"] = filters.release_date.start_date
            if filters.release_date.end_date:
                date_range["lte"] = filters.release_date.end_date

            if date_range:
                filter_clauses.append({"range": {"release_date": date_range}})

        # Rating range filter
        if filters.rating:
            rating_range = {}
            if filters.rating.min_rating is not None:
                rating_range["gte"] = filters.rating.min_rating
            if filters.rating.max_rating is not None:
                rating_range["lte"] = filters.rating.max_rating

            if rating_range:
                filter_clauses.append({"range": {"rating": rating_range}})

        if filters.aggregated_rating:
            agg_rating_range = {}
            if filters.aggregated_rating.min_rating is not None:
                agg_rating_range["gte"] = filters.aggregated_rating.min_rating
            if filters.aggregated_rating.max_rating is not None:
                agg_rating_range["lte"] = filters.aggregated_rating.max_rating

            if agg_rating_range:
                filter_clauses.append(
                    {"range": {"aggregated_rating": agg_rating_range}}
                )

        return filter_clauses

    @staticmethod
    def build_search_body(request: SearchRequest) -> Dict[str, Any]:
        """
        Build complete Elasticsearch query body from SearchRequest.

        Combines multi_match query with optional filters and function_score boosting.
        Uses most_fields type.

        Scoring adjustments:
        - Smooth aggregated_rating contribution via field_value_factor with sqrt modifier
        - Low boost on analyzed keyword text for "unofficial" or "fangame" tokens

        Args:
            request: SearchRequest with query text, size, optional filters, optional explain

        Returns:
            Complete Elasticsearch query body ready for execution
        """
        formatted_fields = QueryBuilder.build_multi_match_fields()
        filter_clauses = QueryBuilder.build_filters(request.filters)

        # Build the core bool query
        bool_query: Dict[str, Any] = {
            "must": [
                {
                    "multi_match": {
                        "query": request.query_text,
                        "fields": formatted_fields,
                        "type": "most_fields",
                    }
                }
            ],
            "should": [
                # Low boost when analyzed keywords match unofficial/fangame tokens
                {
                    "match": {
                        "keywords": {
                            "query": "unofficial fangame",
                            "operator": "or",
                            "boost": 0.1,
                        }
                    }
                },
            ],
        }

        # Add filters if any exist
        if filter_clauses:
            bool_query["filter"] = filter_clauses

        functions = [
            {
                "filter": {"exists": {"field": "rating"}},
                "field_value_factor": {
                    "field": "rating",
                    "factor": 0.15,
                    "modifier": "sqrt",
                    "missing": 0,
                },
            },
            {
                "filter": {"exists": {"field": "aggregated_rating"}},
                "field_value_factor": {
                    "field": "aggregated_rating",
                    "factor": 0.2,
                    "modifier": "sqrt",
                    "missing": 0,
                },
            },
            {
                "filter": {"bool": {"must_not": [{"exists": {"field": "rating"}}]}},
                "script_score": {
                    "script": {
                        "source": "params.factor",
                        "params": {"factor": 0.8},
                    }
                },
            },
            {
                "filter": {"bool": {"must_not": [{"exists": {"field": "aggregated_rating"}}]}},
                "script_score": {
                    "script": {
                        "source": "params.factor",
                        "params": {"factor": 0.5},
                    }
                },
            },
            {
                "filter": {"terms": {"keywords": ["unofficial", "fangame", "fanmade"]}},
                "weight": 0.2,
            },
        ]

        # Build final body with smooth aggregated_rating scoring
        body: Dict[str, Any] = {
            "query": {
                "function_score": {
                    "query": {"bool": bool_query},
                    "functions": functions,
                    "boost_mode": "multiply",
                }
            },
            "size": request.size,
            "explain": request.explain,
        }

        return body

    @staticmethod
    def build_bm25_hybrid_search_body(
        request: SearchRequest, query_vector: List[float]
    ) -> Dict[str, Any]:
        """
        Build a BM25 hybrid search body that adds semantic_embedding matching.

        This uses the same BM25 search configuration as build_search_body,
        but appends an additional dense vector scoring function for semantic relevance.
        The hybrid ranking combines the original BM25 score, metadata boosts,
        and semantic embedding similarity additively.
        """
        body = QueryBuilder.build_search_body(request)
        function_score = body["query"]["function_score"]

        # function_score["score_mode"] = "sum"
        # function_score["boost_mode"] = "sum"
        function_score["functions"].append(
            {
                "script_score": {
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'semantic_embedding') + 1.0",
                        "params": {"query_vector": query_vector},
                    }
                },
                "weight": 2.0,
            }
        )

        return body
