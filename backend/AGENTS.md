---
name: backend-application
description: Information Retrieval API - Multi-algorithm search with BM25 and SVM ranking, weighted fields, advanced filtering for game datasets
---

# Information Retrieval API - Backend Application

## Application Overview

A production-ready **FastAPI application** that provides dual-algorithm search capabilities:

### Core Features
- **Multi-Algorithm Ranking** - Returns results from both BM25 (Elasticsearch native) and SVM (TF-IDF + cosine similarity)
- **Independent Scoring** - Each algorithm produces separate ranked results with its own relevance scores
- **Weighted Field Queries** - Specify search importance per field for BM25 algorithm (e.g., name^2, summary^1)
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
ELASTICSEARCH_INDEX = "games"
DEFAULT_RESULT_SIZE = 5
MAX_RESULT_SIZE = 100
SEARCHABLE_FIELDS = ["name", "summary", "keywords", "themes", ...]
```

#### `models/search.py` - Data Validation
- **`SearchField`** - Field name + weight pair (0.1-10 boost range)
- **`SearchRequest`** - Query text, fields list, optional filters, result size (1-100)
- **`FilterCriteria`** - Genres, platforms, themes, date range, rating range (all ANDed)
- **`GameResult`** - Single game document with all metadata
- **`RankedResult`** - Extends GameResult with `score`, `rank`, and `algorithm` fields
- **`AlgorithmResult`** - Contains results array, total count, execution time for one algorithm
- **`MultiAlgorithmSearchResponse`** - Root response object containing both bm25 and svm results
- **`SearchResponse`** - Legacy response format (deprecated, kept for reference)
- **`ErrorResponse`** - Standardized error format with timestamp

#### `services/query_builder.py` - Elasticsearch DSL Construction
- **`build_multi_match_query()`** - Converts `SearchField` list to Elasticsearch multi_match format with weights
  - Input: `[{"field": "name", "weight": 2}]`
  - Output: `["name^2"]`
- **`build_search_body()`** - Constructs BM25 query with weighted fields and filters
- **`build_match_query_for_ranking()`** - Constructs broader match query for SVM ranking (no field weights, OR logic)
- **`build_filters()`** - Converts `FilterCriteria` to Elasticsearch must clauses (shared by all algorithms)
- Supports all filter types and ranges

#### `services/search.py` - Multi-Algorithm Query Execution
- **`execute_search()`** - Main entry point, delegates to `execute_multi_algorithm_search()`
  - Returns `MultiAlgorithmSearchResponse` with both algorithms
- **`execute_multi_algorithm_search()`** - Orchestrates BM25 + SVM ranking
  - Calls `_execute_bm25()` and `_execute_svm()` sequentially
  - Returns combined results from both algorithms
  - Includes error handling for each algorithm
- **`_execute_bm25()`** - Elasticsearch native BM25 search
  - Uses field-weighted multi_match query
  - Returns Elasticsearch relevance scores (0-100 normalized)
  - Includes execution time tracking
- **`_execute_svm()`** - TF-IDF + cosine similarity ranking
  - Fetches documents via broad match query
  - Uses `RankingService` to calculate SVM scores
  - Returns sorted results by SVM score
  - Includes execution time tracking
- **`_parse_es_response()`** - Extracts documents and scores from ES response
- **`_parse_hit()`** - Converts single ES hit to `GameResult` model
- **`_game_result_to_ranked_result()`** - Adds BM25 ranking metadata
- **`_create_ranked_result()`** - Adds SVM ranking metadata

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
- `bm25.results` - Results ranked by Elasticsearch BM25 algorithm (field weights applied)
- `svm.results` - Results ranked by TF-IDF + cosine similarity (equal importance)
- `results[].score` - Algorithm-specific relevance score (0-100)
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
- Edit `QueryBuilder.build_search_body()` to change default weights
- Adjust `QueryBuilder.build_multi_match_query()` weight format logic
- Test with `execute_search()` to verify BM25 ranking changes
- Performance impact visible in `execution_time_ms`

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
1. Check `SearchRequest` fields parameter - different fields for BM25
2. SVM uses broader fields (name, summary, keywords, themes, genres, category) defined in `build_match_query_for_ranking()`
3. BM25 uses only requested fields with user-specified weights
4. Different ranking is normal - different algorithms = different scoring
5. Compare scores: BM25 = Elasticsearch internal scoring, SVM = TF-IDF (0-100 normalized)

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
