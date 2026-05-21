---
name: backend-application
description: Information Retrieval API - Multi-algorithm search with BM25 and SVM ranking, config-driven field weights, advanced filtering for game datasets
---

# Information Retrieval API - Backend Application

## Application Overview

A production-ready **FastAPI application** that provides dual-algorithm search capabilities:

### Core Features
- **Multi-Algorithm Ranking** - Returns results from both BM25 (Elasticsearch native) and SVM (TF-IDF + cosine similarity)
- **Independent Scoring** - Each algorithm produces separate ranked results with its own relevance scores
- **Weighted Field Queries** - `multi_match` uses `DEFAULT_SEARCH_FIELD_WEIGHTS` in `config.py` (server-side boosts; clients do not send field weights)
- **Advanced Filtering** - Filter by genres, platforms, themes, player perspectives, game modes, date ranges, and ratings (unified across both algorithms)
- **Type-safe requests/responses** - Pydantic validation with detailed error messages
- **Performance Tracking** - Execution time measured separately for each algorithm

**Target Domain**: Game dataset search and retrieval from a structured Elasticsearch index using multiple ranking strategies

**Key Algorithms**:
- **BM25** - Elasticsearch's native relevance algorithm with field weighting support
- **SVM** - TF-IDF term frequency with cosine similarity for alternative ranking perspective

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
│   ├── search.py                # Multi-algorithm search execution
│   ├── ranking.py               # SVM ranking (TF-IDF + cosine similarity)
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
BM25_INDEX_NAME = "games_bm25"
SVM_INDEX_NAME = "games_svm"
DEFAULT_RESULT_SIZE = 5
MAX_RESULT_SIZE = 1000
SEARCHABLE_FIELDS = ["name", "summary", "keywords", "themes", ...]
DEFAULT_SEARCH_FIELD_WEIGHTS = [("name", 3.0), ("summary", 2.0), ...]  # multi_match fields^boost
```

#### `models/search.py` - Data Validation
- **`SearchRequest`** - Query text, optional `explain`, optional filters, result size (1-1000); no per-request field list
- **`FilterCriteria`** - Genres, platforms, themes, date range, rating range (all ANDed)
- **`GameResult`** - Single game document with all metadata
- **`RankedResult`** - Extends GameResult with `score`, `rank`, and `algorithm` fields
- **`AlgorithmResult`** - Contains results array, total count, execution time for one algorithm
- **`MultiAlgorithmSearchResponse`** - Root response object containing both bm25 and svm results
- **`SearchResponse`** - Legacy response format (deprecated, kept for reference)
- **`ErrorResponse`** - Standardized error format with timestamp

#### `services/query_builder.py` - Elasticsearch DSL Construction
- **`build_multi_match_fields()`** - Builds `multi_match.fields` from `config.DEFAULT_SEARCH_FIELD_WEIGHTS`
  - Example output: `["name^3.0", "summary^2.0", "keywords", ...]`
- **`build_search_body()`** - Constructs query (bool + `function_score`) using those fields and request filters
- **`build_filters()`** - Converts `FilterCriteria` to Elasticsearch filter clauses (shared by all algorithms)
- Supports all filter types and ranges

#### `services/search.py` - Multi-Algorithm Query Execution
- **`execute_search()`** - Main entry point, delegates to `execute_multi_algorithm_search()`
  - Returns `MultiAlgorithmSearchResponse` with both algorithms
- **`execute_multi_algorithm_search()`** - Orchestrates BM25 + SVM ranking
  - Calls `_execute_bm25()` and `_execute_svm()` sequentially
  - Returns combined results from both algorithms
  - Includes error handling for each algorithm
- **`_execute_bm25()`** - Elasticsearch native BM25 search
  - Uses field-weighted `multi_match` (weights from `DEFAULT_SEARCH_FIELD_WEIGHTS`)
  - Returns Elasticsearch relevance scores
  - Includes execution time tracking
- **`_execute_svm()`** - Same query body against the SVM index (`games_svm`)
  - Scripted similarity (`tfidf_salton`) produces TF-IDF-style scores in Elasticsearch
  - When `SearchRequest.explain` is true, attaches per-hit explanations to `AlgorithmResult.explanations`
- **`_parse_es_response()`** - Extracts documents and scores from ES response
- **`_parse_hit()`** - Converts single ES hit to `GameResult` model
- **`_game_result_to_ranked_result()`** - Adds algorithm metadata (`bm25` / `svm`)

#### `services/ranking.py` - SVM Ranking Service (TF-IDF + Cosine Similarity)
- **`tokenize(text)`** - Lowercase tokenization with whitespace splitting
- **`calculate_tfidf_scores(query_text, documents)`** - Main TF-IDF calculation
  - Computes term frequency per document
  - Calculates inverse document frequency
  - Combines TF * IDF per term
  - Returns normalized scores (0-100)
- **`calculate_cosine_similarity(query_text, documents)`** - Vector-based similarity
  - Builds term frequency vectors for query and documents
  - Computes dot product and vector magnitudes
  - Returns cosine similarity scores (0-100)
- **`rank_documents(query_text, documents, algorithm="svm")`** - Main ranking method
  - Combines TF-IDF + cosine similarity (equal weight average)
  - Returns final scores in 0-100 range
- **`add_ranking_metadata(documents, scores, algorithm)`** - Sorting and ranking
  - Sorts documents by score descending
  - Assigns rank positions (1-based)
  - Returns (document, score, rank) tuples

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
  "size": 10,
  "explain": false,
  "filters": {
    "genres": ["Shooter"],
    "platforms": ["PC"],
    "release_date": {"start_date": "2020-01-01", "end_date": "2023-12-31"},
    "rating": {"min_rating": 70}
  }
}
```

Field boosts for `multi_match` are not part of the request; they come from `DEFAULT_SEARCH_FIELD_WEIGHTS` in `config.py`.

### Search Response (Multi-Algorithm Format)

The response now contains results from both BM25 and SVM algorithms:

```json
{
  "bm25": {
    "results": [
      {
        "id": "game123",
        "name": "Game Title",
        "summary": "...",
        "score": 9.5,
        "rank": 1,
        "algorithm": "bm25",
        "genres": ["Shooter", "Action"],
        "platforms": ["PC"],
        "rating": 85.2,
        "release_date": "2021-06-15"
      },
      {
        "id": "game456",
        "name": "Another Game",
        "summary": "...",
        "score": 7.8,
        "rank": 2,
        "algorithm": "bm25",
        ...
      }
    ],
    "total": 42,
    "execution_time_ms": 120
  },
  "svm": {
    "results": [
      {
        "id": "game456",
        "name": "Another Game",
        "summary": "...",
        "score": 92.5,
        "rank": 1,
        "algorithm": "svm",
        "genres": ["Shooter"],
        "platforms": ["PC"],
        "rating": 78.5,
        "release_date": "2020-03-10"
      },
      {
        "id": "game123",
        "name": "Game Title",
        "summary": "...",
        "score": 88.2,
        "rank": 2,
        "algorithm": "svm",
        ...
      }
    ],
    "total": 42,
    "execution_time_ms": 45
  }
}
```

**Response Structure**:
- `bm25.results` - Results ranked by Elasticsearch BM25 (field weights from `DEFAULT_SEARCH_FIELD_WEIGHTS`)
- `svm.results` - Same query against the SVM index; scores from scripted TF-IDF similarity
- `results[].score` - Algorithm-specific relevance score (raw Elasticsearch `_score`)
- `bm25.explanations` / `svm.explanations` - Present when `"explain": true` in the request
- `results[].rank` - Position in algorithm's ranking (1 = highest score)
- `results[].algorithm` - Which algorithm produced this ranking
- `total` - Total matching documents (same for both algorithms due to unified filters)
- `execution_time_ms` - Time in milliseconds for that algorithm's execution

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
- `SearchRequest` rejects unknown keys (`extra="forbid"`)
- Result size bounds enforced (1-1000)
- Default search field weights validated at import time in `config.py`

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
1. Add new field to `SEARCHABLE_FIELDS` in `config.py` and to index mappings if needed
2. Add an entry to `DEFAULT_SEARCH_FIELD_WEIGHTS` (field name + weight in `[0.1, 10]`) so it participates in `multi_match`

### Adding Filter Types
1. Add field to `FilterCriteria` in `models/search.py` with validation
2. Add filter logic to `QueryBuilder.build_filters()` in `services/query_builder.py`
3. Optionally add to `FiltersService.FILTER_FIELDS` if values should be discoverable

### Elasticsearch Integration
- Index names configured in `config.py` (`BM25_INDEX_NAME`, `SVM_INDEX_NAME`)
- Connection validated at startup
- Queries use `multi_match` with fields/boosts from `DEFAULT_SEARCH_FIELD_WEIGHTS`
- Filters applied as `filter` context on the bool query (AND logic)

---

## Common Tasks for Agents

### Task: Understand Multi-Algorithm Search Flow
1. Search request comes to `/search` endpoint in `main.py`
2. Calls `SearchService.execute_multi_algorithm_search()`
3. Runs `_execute_bm25()` → Elasticsearch weighted multi_match → BM25 scores
4. Runs `_execute_svm()` → Elasticsearch broad match → `RankingService` TF-IDF ranking
5. Both algorithms apply same filters from `QueryBuilder.build_filters()`
6. Results combined into `MultiAlgorithmSearchResponse` with nested bm25/svm keys

### Task: Add New Ranking Algorithm
1. Create new class in `services/ranking.py` or new file
2. Implement methods: `calculate_scores()`, `rank_documents()`
3. Add corresponding `_execute_<algorithm>()` method in `SearchService`
4. Add algorithm result to `MultiAlgorithmSearchResponse` model in `models/search.py`
5. Update endpoint docstring with new response structure

### Task: Modify BM25 Field Weighting
- Edit `DEFAULT_SEARCH_FIELD_WEIGHTS` in `config.py` (shared by BM25 and SVM query bodies)
- Optionally adjust `QueryBuilder.build_multi_match_fields()` formatting rules
- Test with `execute_search()` to verify ranking changes; check `execution_time_ms`

### Task: Tune SVM Ranking
- Edit `RankingService.rank_documents()` for algorithm parameter
- Adjust weights between TF-IDF and cosine similarity (currently equal)
- Modify tokenization in `tokenize()` for different text preprocessing
- Add stop word removal or stemming for better relevance matching

### Task: Add Filtering Option
1. Add field to `FilterCriteria` model in `models/search.py` with validation
2. Add filter clause to `QueryBuilder.build_filters()` in `services/query_builder.py`
3. This applies to both BM25 and SVM algorithms automatically
4. Optionally add to `FiltersService.FILTER_FIELDS` if UI dropdown needed

### Task: Optimize Query Performance
- Current typical execution: BM25 ~80-150ms, SVM ~50-100ms, Total ~150-300ms
- Profile with `execution_time_ms` values returned in response
- For BM25: Optimize query complexity, reduce number of fields, adjust Elasticsearch settings
- For SVM: RankingService TF-IDF calculation is O(n*m) where n=docs, m=terms; optimize tokenization
- Consider parallel execution of algorithms with asyncio

### Task: Debug Multi-Algorithm Results Discrepancy
1. Both algorithms use the same `multi_match` fields and boosts from `DEFAULT_SEARCH_FIELD_WEIGHTS`
2. BM25 and SVM differ mainly by index similarity (BM25 default vs scripted TF-IDF on `games_svm`)
3. Different ranking is normal: same query text, different scoring functions
4. Use `"explain": true` to inspect per-hit score breakdowns in `AlgorithmResult.explanations`

### Task: Debug Failed Search
- Check `validate_elasticsearch_connection()` passes at startup
- Verify `SEARCHABLE_FIELDS` in `config.py` match actual index fields
- Review Pydantic validation errors for malformed requests
- If BM25 fails: Check Elasticsearch logs for query DSL errors
- If SVM fails: Check `RankingService` tokenization and TF-IDF calculation
- Look at `execution_time_ms` for timeout indicators

### Task: Return Single Algorithm Results (Backward Compatibility)
- Endpoint currently returns `MultiAlgorithmSearchResponse` (breaking change)
- To support old clients: Create `/search/legacy` endpoint
- Have it call `execute_search()` and return only `SearchResponse` with BM25 results
- Alternative: Add optional query parameter `?format=legacy` to existing endpoint
