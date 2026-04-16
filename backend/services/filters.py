"""
Filters service for fetching available filter values.
Retrieves unique values from Elasticsearch index for frontend filter dropdowns.
"""

from typing import Dict, List, Set
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError


class FiltersService:
    """
    Service for fetching available filter values from Elasticsearch.
    Used to populate frontend filter dropdowns.
    """

    FILTER_FIELDS = [
        "genres",
        "game_modes",
        "platforms",
        "player_perspectives",
        "themes",
    ]

    @staticmethod
    def get_all_filters(es_client: Elasticsearch, index_name: str) -> Dict[str, List[str]]:
        """
        Fetch all unique filter values from the Elasticsearch index.
        
        Args:
            es_client: Elasticsearch client instance
            index_name: Name of the index to search
            
        Returns:
            Dictionary with filter field names as keys and sorted unique values as values
            
        Raises:
            ConnectionError: If ES connection fails
            NotFoundError: If index doesn't exist
        """
        try:
            filters_data = {}

            for field in FiltersService.FILTER_FIELDS:
                unique_values = FiltersService._get_field_values(
                    es_client, index_name, field
                )
                filters_data[field] = sorted(unique_values)

            return filters_data

        except ConnectionError as e:
            raise ConnectionError(
                f"Failed to connect to Elasticsearch: {str(e)}"
            )
        except NotFoundError as e:
            raise NotFoundError(
                f"Index '{index_name}' not found in Elasticsearch"
            )
        except Exception as e:
            raise ValueError(
                f"Failed to fetch filters: {str(e)}"
            )

    @staticmethod
    def _get_field_values(
        es_client: Elasticsearch,
        index_name: str,
        field_name: str
    ) -> Set[str]:
        """
        Get unique values for a specific field using Elasticsearch aggregations.
        
        Args:
            es_client: Elasticsearch client instance
            index_name: Name of the index to search
            field_name: Name of the field to aggregate
            
        Returns:
            Set of unique values in the field
        """
        try:
            # Use terms aggregation to get all unique values
            # Bucket size is set high to capture all potential values
            query_body = {
                "size": 0,
                "aggs": {
                    "unique_values": {
                        "terms": {
                            "field": field_name,
                            "size": 10000
                        }
                    }
                }
            }

            response = es_client.search(index=index_name, body=query_body)

            # Extract unique values from aggregation buckets
            buckets = response.get("aggregations", {}).get("unique_values", {}).get("buckets", [])
            unique_values = {bucket["key"] for bucket in buckets if bucket["key"]}

            return unique_values

        except Exception as e:
            # If aggregation fails, return empty set for this field
            print(f"⚠️  Warning: Could not fetch values for field '{field_name}': {str(e)}")
            return set()
