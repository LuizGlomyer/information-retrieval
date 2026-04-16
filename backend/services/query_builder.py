"""
Query builder for constructing Elasticsearch queries.
Converts SearchRequest models to Elasticsearch query DSL.
"""

from typing import Dict, Any, List, Optional
from models.search import SearchRequest, SearchField, FilterCriteria


class QueryBuilder:
    """
    Builds Elasticsearch query bodies from search requests.
    Handles multi_match queries with field weighting and filtering.
    """

    @staticmethod
    def build_multi_match_query(fields: List[SearchField]) -> Dict[str, Any]:
        """
        Convert list of SearchField to Elasticsearch multi_match format.
        
        Converts:
            [{"field": "name", "weight": 2}, {"field": "summary", "weight": 1}]
        To:
            ["name^2", "summary^1"]
        
        Args:
            fields: List of SearchField with field names and weights
            
        Returns:
            List of formatted field strings with weights
        """
        formatted_fields = []
        for field in fields:
            weight = field.weight if field.weight != 1 else 1
            if weight == 1:
                formatted_fields.append(field.field)
            else:
                formatted_fields.append(f"{field.field}^{weight}")
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
            filter_clauses.append({
                "terms": {"genres": filters.genres}
            })

        if filters.game_modes:
            filter_clauses.append({
                "terms": {"game_modes": filters.game_modes}
            })

        if filters.platforms:
            filter_clauses.append({
                "terms": {"platforms": filters.platforms}
            })

        if filters.player_perspectives:
            filter_clauses.append({
                "terms": {"player_perspectives": filters.player_perspectives}
            })

        if filters.themes:
            filter_clauses.append({
                "terms": {"themes": filters.themes}
            })

        # Date range filter
        if filters.release_date:
            date_range = {}
            if filters.release_date.start_date:
                date_range["gte"] = filters.release_date.start_date
            if filters.release_date.end_date:
                date_range["lte"] = filters.release_date.end_date

            if date_range:
                filter_clauses.append({
                    "range": {"release_date": date_range}
                })

        # Rating range filter
        if filters.rating:
            rating_range = {}
            if filters.rating.min_rating is not None:
                rating_range["gte"] = filters.rating.min_rating
            if filters.rating.max_rating is not None:
                rating_range["lte"] = filters.rating.max_rating

            if rating_range:
                filter_clauses.append({
                    "range": {"aggregated_rating": rating_range}
                })

        return filter_clauses

    @staticmethod
    def build_search_body(request: SearchRequest) -> Dict[str, Any]:
        """
        Build complete Elasticsearch query body from SearchRequest.
        
        Combines multi_match query with optional filters.
        Uses best_fields type to find documents where query terms appear together.
        
        Args:
            request: SearchRequest with query text, fields, size, and optional filters
            
        Returns:
            Complete Elasticsearch query body ready for execution
            
        Example:
            {
                "query": {
                    "bool": {
                        "must": [{
                            "multi_match": {
                                "query": "action adventure",
                                "fields": ["name^3", "summary^1"],
                                "type": "best_fields"
                            }
                        }],
                        "filter": [...]  # optional
                    }
                },
                "size": 10
            }
        """
        formatted_fields = QueryBuilder.build_multi_match_query(request.fields)
        filter_clauses = QueryBuilder.build_filters(request.filters)

        # Build the bool query
        bool_query: Dict[str, Any] = {
            "must": [{
                "multi_match": {
                    "query": request.query_text,
                    "fields": formatted_fields,
                    "type": "best_fields"
                }
            }]
        }

        # Add filters if any exist
        if filter_clauses:
            bool_query["filter"] = filter_clauses

        # Build final body
        body: Dict[str, Any] = {
            "query": {"bool": bool_query},
            "size": request.size
        }

        return body
