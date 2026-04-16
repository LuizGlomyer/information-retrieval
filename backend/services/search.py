"""
Search service for executing Elasticsearch queries.
Handles search execution, error handling, and response mapping.
"""

from typing import List, Dict, Any
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError, BadRequestError
from models.search import SearchRequest, SearchResponse, GameResult
from services.query_builder import QueryBuilder


class SearchService:
    """
    Service for executing Elasticsearch searches.
    Encapsulates all ES interactions and response handling.
    """

    @staticmethod
    def execute_search(
        es_client: Elasticsearch,
        index_name: str,
        request: SearchRequest
    ) -> SearchResponse:
        """
        Execute a search query against Elasticsearch.
        
        Args:
            es_client: Elasticsearch client instance
            index_name: Name of the index to search
            request: SearchRequest with query parameters
            
        Returns:
            SearchResponse with results, total count, and execution time
            
        Raises:
            ConnectionError: If ES connection fails
            NotFoundError: If index doesn't exist
            BadRequestError: If query is malformed
            ValueError: If response parsing fails
        """
        try:
            # Build the Elasticsearch query body
            query_body = QueryBuilder.build_search_body(request)

            # Execute the search
            response = es_client.search(index=index_name, body=query_body)

            # Parse and map results
            results = SearchService._parse_response(response)

            return results

        except ConnectionError as e:
            raise ConnectionError(
                f"Failed to connect to Elasticsearch: {str(e)}"
            )
        except NotFoundError as e:
            raise NotFoundError(
                f"Index '{index_name}' not found in Elasticsearch"
            )
        except BadRequestError as e:
            raise BadRequestError(
                f"Invalid search query: {str(e)}"
            )
        except Exception as e:
            raise ValueError(
                f"Search execution failed: {str(e)}"
            )

    @staticmethod
    def _parse_response(es_response: Dict[str, Any]) -> SearchResponse:
        """
        Parse Elasticsearch response into SearchResponse model.
        
        Args:
            es_response: Raw Elasticsearch response dictionary
            
        Returns:
            SearchResponse with parsed results
            
        Raises:
            ValueError: If response structure is invalid
        """
        try:
            # Extract metadata
            total_hits = es_response.get("hits", {}).get("total", {})
            
            # Handle both ES 7 and ES 8+ response formats
            if isinstance(total_hits, dict):
                total_count = total_hits.get("value", 0)
            else:
                total_count = total_hits

            took_ms = es_response.get("took", 0)

            # Parse hit documents
            hits = es_response.get("hits", {}).get("hits", [])
            results = [
                SearchService._parse_hit(hit)
                for hit in hits
            ]

            return SearchResponse(
                results=results,
                total=total_count,
                took_ms=took_ms
            )

        except (KeyError, TypeError) as e:
            raise ValueError(
                f"Failed to parse Elasticsearch response: {str(e)}"
            )

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
            keywords=source.get("keywords"),
            release_date=source.get("release_date"),
        )
