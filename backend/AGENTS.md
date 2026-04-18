---
name: backend-application
description: Information Retrieval API - FastAPI application providing Elasticsearch-powered search with weighted fields and advanced filtering for game datasets
---

# Information Retrieval API - Backend Application

## Application Overview

A production-ready **FastAPI application** that provides dynamic Elasticsearch search capabilities with:
- **Weighted field queries** - Specify search importance per field (e.g., name^2, summary^1)
- **Advanced filtering** - Filter by genres, platforms, themes, player perspectives, game modes, date ranges, and ratings
- **Type-safe requests/responses** - Pydantic validation with detailed error messages
- **Structured metadata** - Execution time, total hits, and result counts

**Target Domain**: Game dataset search and retrieval from a structured Elasticsearch index

---

## Architecture & Modules

### Directory Structure
```
backend/
├── main.py                      # FastAPI app initialization, endpoints
├── config.py                    # Configuration and constants
├── models/search.py             # Pydantic request/response models
├── services/
│   ├── query_builder.py         # Elasticsearch query DSL construction
│   ├── search.py                # Search execution and result mapping
│   └── filters.py               # Filter value retrieval for dropdowns
└── pyproject.toml               # Dependencies
```

### Key Modules

#### `main.py` - Application Entry Point
- **`validate_elasticsearch_connection()`** - Validates ES connectivity at startup; exits if connection fails
- **`validate_index_exists()`** - Ensures the required index exists
- **`create_app()`** - Configures FastAPI with endpoints and state management
- **Endpoints**:
  - `GET /health` - Health check and connectivity status
  - `POST /search` - Execute weighted field search with optional filters
  - `GET /filters` - Retrieve available filter values for UI dropdowns

#### `config.py` - Centralized Settings
```python
ELASTICSEARCH_HOST = "localhost"
ELASTICSEARCH_PORT = 9200
ELASTICSEARCH_INDEX = "games"
DEFAULT_RESULT_SIZE = 5
MAX_RESULT_SIZE = 100
SEARCHABLE_FIELDS = ["name", "summary", "keywords", "themes", ...]
```

#### `models/search.py` - Data Validation
- **`SearchField`** - Field name + weight pair (0.1-10 boost range)
- **`SearchRequest`** - Query text, fields list, optional filters, result size (1-100)
- **`FilterCriteria`** - Genres, platforms, themes, date range, rating range (all ANDed)
- **`SearchResponse`** - Results array, total hit count, execution time, query metadata
- **`ErrorResponse`** - Standardized error format with timestamp

#### `services/query_builder.py` - Elasticsearch DSL Construction
- **`build_multi_match_query()`** - Converts `SearchField` list to Elasticsearch multi_match format
  - Input: `[{"field": "name", "weight": 2}]`
  - Output: `["name^2"]`
- **`build_filters()`** - Converts `FilterCriteria` to Elasticsearch must clauses
- Supports all filter types and ranges

#### `services/search.py` - Query Execution
- **`execute_search()`** - Main method
  - Builds ES query via `QueryBuilder`
  - Executes against Elasticsearch
  - Maps results to `SearchResponse` model
  - Handles ES exceptions (ConnectionError, NotFoundError, BadRequestError)
- **`_parse_response()`** - Extracts and normalizes ES response data

#### `services/filters.py` - Filter Value Discovery
- **`get_all_filters()`** - Returns unique values for all filter fields
- **`FILTER_FIELDS`** - Supported filter categories: `genres`, `game_modes`, `platforms`, `player_perspectives`, `themes`
- Returns sorted, deduplicated values for UI dropdowns

---

## Request/Response Examples

### Search Request
```json
{
  "query_text": "action shooter",
  "fields": [
    {"field": "name", "weight": 3},
    {"field": "summary", "weight": 1}
  ],
  "size": 10,
  "filters": {
    "genres": ["Shooter"],
    "platforms": ["PC"],
    "date_range": {"start_date": "2020-01-01", "end_date": "2023-12-31"},
    "rating_range": {"min_rating": 70}
  }
}
```

### Search Response
```json
{
  "query_text": "action shooter",
  "total": 42,
  "results": [
    {
      "id": "game123",
      "name": "Game Title",
      "summary": "...",
      "score": 9.5,
      "genres": ["Shooter", "Action"],
      "platforms": ["PC"],
      "rating": 85.2,
      "release_date": "2021-06-15"
    }
  ],
  "execution_time_ms": 125,
  "filters_applied": 3
}
```

### Filters Response
```json
{
  "genres": ["Action", "Adventure", "Puzzle", "RPG", "Shooter", ...],
  "game_modes": ["Campaign", "Co-op", "Multiplayer", ...],
  "platforms": ["PC", "PlayStation", "Xbox", "Switch", ...],
  "player_perspectives": ["First Person", "Third Person", ...],
  "themes": ["Horror", "Fantasy", "Sci-Fi", ...]
}
```

---

## Dependencies

**Core Stack**:
- `fastapi>=0.135.3` - Web framework
- `elasticsearch>=9.3.0` - Search client
- `pydantic>=2.13.0` - Data validation
- `uvicorn>=0.44.0` - ASGI server

**Python**: >=3.14

---

## Design Patterns

### Separation of Concerns
- **Models** - Data validation and schema definition
- **Services** - Business logic (query building, search execution)
- **Endpoints** - Request handling and response formatting

### Type Safety
- All requests/responses validated via Pydantic
- Field validators ensure searchable fields exist
- Weight ranges enforced (0.1-10)
- Result size bounds enforced (1-100)

### Error Handling
- Pydantic ValidationError → 422 Unprocessable Entity
- Elasticsearch ConnectionError → 503 Service Unavailable
- BadRequestError (malformed query) → 400 Bad Request
- NotFoundError (missing index) → 404 Not Found
- All errors include timestamp, error message, and context

### Stateless Design
- Elasticsearch client passed to services as dependency
- No in-memory state except app configuration
- Each request independently processed

---

## Development Notes

### Extending Search Capabilities
1. Add new field to `SEARCHABLE_FIELDS` in `config.py`
2. Update Elasticsearch mapping if necessary
3. Fields automatically available for weighted search

### Adding Filter Types
1. Add field to `FilterCriteria` in `models/search.py` with validation
2. Add filter logic to `QueryBuilder.build_filters()` in `services/query_builder.py`
3. Optionally add to `FiltersService.FILTER_FIELDS` if values should be discoverable

### Elasticsearch Integration
- Index name configured in `config.py` (default: "games")
- Connection validated at startup
- Queries use multi_match for weighted field search
- Filters applied as must clauses (AND logic)

---

## Common Tasks for Agents

### Task: Implement Search Feature
- Review `models/search.py` for request/response structure
- Use `SearchService.execute_search()` from endpoint
- `QueryBuilder` handles ES DSL translation

### Task: Add Filtering Option
- Update `FilterCriteria` model with new field and validation
- Add filter clause to `QueryBuilder.build_filters()`
- Test against running Elasticsearch instance

### Task: Optimize Query Performance
- Review `QueryBuilder.build_multi_match_query()` for field weighting logic
- Elasticsearch stats available in `SearchResponse.execution_time_ms`
- Index mappings and analyzer settings in Elasticsearch

### Task: Debug Failed Search
- Check `validate_elasticsearch_connection()` passes at startup
- Verify `SEARCHABLE_FIELDS` in `config.py` match actual index fields
- Review Pydantic validation errors for malformed requests
- Check Elasticsearch logs for query parsing issues
