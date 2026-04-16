"""
Application configuration and constants.
Centralize all settings for Elasticsearch connection and API limits.
"""

# Elasticsearch Configuration
ELASTICSEARCH_HOST = "localhost"
ELASTICSEARCH_PORT = 9200
ELASTICSEARCH_INDEX = "games"

# Search Limits
DEFAULT_RESULT_SIZE = 5
MAX_RESULT_SIZE = 100
MIN_RESULT_SIZE = 1

# Search Query Defaults
DEFAULT_QUERY_TYPE = "best_fields"
DEFAULT_FUZZINESS = "AUTO"

# Supported fields for searching and filtering
SEARCHABLE_FIELDS = [
    "name",
    "summary",
    "keywords",
    "themes",
    "category",
    "genres",
]

FILTERABLE_FIELDS = {
    "category": "keyword",
    "genres": "keyword",
    "platforms": "keyword",
    "themes": "keyword",
    "release_date": "date",
    "rating": "float",
    "aggregated_rating": "float",
}
