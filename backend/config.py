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

# Supported fields for searching
SEARCHABLE_FIELDS = [
    "name",
    "summary",
    "keywords",
    "themes",
    "category",
    "genres",
    "platforms",
    "player_perspectives",
    "game_modes",
]
