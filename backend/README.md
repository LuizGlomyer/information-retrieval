# Information Retrieval API - Backend

A high-performance, production-ready FastAPI application for dynamic Elasticsearch searches with weighted field queries and filtering.

## 🚀 Features

- **Dynamic Search Queries**: Specify which fields to search and their weight/importance
- **Weighted Field Matching**: Boost relevance for specific fields (e.g., name^3, summary^1)
- **Advanced Filtering**: Filter by category, genres, platforms, themes, date ranges, and ratings
- **Pydantic Validation**: Automatic request validation with detailed error messages
- **Structured Responses**: Consistent JSON response format with metadata
- **Error Handling**: Comprehensive error handling with clear HTTP status codes
- **OpenAPI Documentation**: Auto-generated API docs at `/docs`

## 📋 Architecture

```
backend/
├── main.py                 # FastAPI app, health check, search endpoint
├── config.py               # Configuration, constants, limits
├── models/
│   ├── __init__.py
│   └── search.py           # Pydantic models for request/response
├── services/
│   ├── __init__.py
│   ├── query_builder.py    # Elasticsearch query construction
│   └── search.py           # Search execution and response mapping
├── pyproject.toml          # Dependencies
└── README.md               # This file
```

### Design Principles

- **Separation of Concerns**: Models, services, and endpoints are cleanly separated
- **Type Safety**: Pydantic models ensure validated, type-checked requests/responses
- **Reusability**: Services can be imported and used independently
- **Modularity**: Easy to extend with new endpoints or query types
- **Error Resilience**: Graceful error handling with informative messages

## 🛠️ Setup

### Install Dependencies

```bash
cd backend
pip install -r ../requirements.txt
# Or if using pyproject.toml:
pip install -e .
```

Required packages:
- `fastapi>=0.135.3`
- `elasticsearch>=9.3.0`
- `pydantic>=2.13.0`
- `uvicorn>=0.44.0`

### Start Elasticsearch

Make sure Elasticsearch is running locally on `localhost:9200`:

```bash
# Using Docker
docker-compose up elasticsearch

# Or check the repository root docker-compose.yml
```

### Run the Application

```bash
# Development with auto-reload
uvicorn main:app --reload

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

## 📚 API Endpoints

### Health Check

```
GET /health
```

Returns the status of the API and Elasticsearch connection.

**Response:**
```json
{
  "status": "healthy",
  "elasticsearch": "connected",
  "index": "games"
}
```

### Dynamic Search

```
POST /search
```

Execute a dynamic search with weighted fields and optional filtering.

#### Request Body

```json
{
  "query_text": "action adventure",
  "fields": [
    {"field": "name", "weight": 3},
    {"field": "summary", "weight": 1},
    {"field": "keywords"}
  ],
  "size": 10,
  "filters": {
    "genres": ["Action", "Adventure"],
    "platforms": ["PC"],
    "themes": ["Sci-Fi"],
    "game_modes": ["Single player"],
    "release_date": {
      "start_date": "2020-01-01",
      "end_date": "2023-12-31"
    },
    "rating": {
      "min_rating": 70,
      "max_rating": 100
    }
  }
}
```

#### Parameters

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query_text` | string | ✓ | - | Search query (1-500 characters) |
| `fields` | array | ✓ | - | Fields to search with optional weights |
| `fields[].field` | string | ✓ | - | Field name (e.g., "name", "summary") |
| `fields[].weight` | number | ✗ | 1 | Weight/boost factor (0.1-10) |
| `size` | integer | ✗ | 5 | Results per page (1-100) |
| `filters` | object | ✗ | null | Optional filtering criteria |
| `filters.genres` | array | ✗ | - | Filter by any of these genres |
| `filters.game_modes` | array | ✗ | - | Filter by any of these game modes |
| `filters.platforms` | array | ✗ | - | Filter by any of these platforms |
| `filters.player_perspectives` | array | ✗ | - | Filter by any of these player perspectives |
| `filters.themes` | array | ✗ | - | Filter by any of these themes |
| `filters.release_date.start_date` | string | ✗ | - | Start date (ISO format) |
| `filters.release_date.end_date` | string | ✗ | - | End date (ISO format) |
| `filters.rating.min_rating` | number | ✗ | - | Minimum rating (0-100) |
| `filters.rating.max_rating` | number | ✗ | - | Maximum rating (0-100) |

#### Response

```json
{
  "results": [
    {
      "id": "123",
      "name": "Game Name",
      "summary": "Game description...",
      "category": "main",
      "rating": 8.5,
      "aggregated_rating": 82,
      "genres": ["Action", "Adventure"],
      "themes": ["Open World"],
      "platforms": ["PC", "PlayStation"],
      "keywords": ["action", "adventure"],
      "release_date": "2021-05-15"
    }
  ],
  "total": 42,
  "took_ms": 125
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `results` | array | Matching game documents |
| `results[].id` | string | Game ID |
| `results[].name` | string | Game name |
| `results[].summary` | string | Game description |
| `results[].category` | string | Game category |
| `results[].rating` | number | User rating |
| `results[].aggregated_rating` | number | Aggregated rating |
| `results[].genres` | array | Genres |
| `results[].themes` | array | Themes |
| `results[].platforms` | array | Platforms |
| `results[].keywords` | array | Keywords |
| `results[].release_date` | string | Release date |
| `total` | integer | Total matching documents |
| `took_ms` | integer | Query execution time (milliseconds) |

### Get Available Filters

```
GET /filters
```

Retrieve all available filter values for populating frontend filter dropdowns.

#### Response

```json
{
  "genres": ["Action", "Adventure", "RPG", "Strategy", ...],
  "game_modes": ["Single player", "Multiplayer", "Cooperative", ...],
  "platforms": ["PC", "PlayStation", "Xbox", "Nintendo", ...],
  "player_perspectives": ["First person", "Third person", "Top-down", ...],
  "themes": ["Fantasy", "Sci-Fi", "Horror", "Historical", ...]
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `genres` | array | All available genres |
| `game_modes` | array | All available game modes |
| `platforms` | array | All available platforms |
| `player_perspectives` | array | All available player perspectives |
| `themes` | array | All available themes |

## 📝 Examples

### Simple Search (One Field)

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "zelda",
    "fields": [{"field": "name"}],
    "size": 5
  }'
```

### Weighted Search (Multiple Fields)

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "action game",
    "fields": [
      {"field": "name", "weight": 3},
      {"field": "summary", "weight": 1},
      {"field": "keywords", "weight": 2}
    ],
    "size": 10
  }'
```

### Get Filter Values

```bash
curl "http://localhost:8000/filters"
```

### Search with Filters

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "open world",
    "fields": [
      {"field": "name", "weight": 2},
      {"field": "summary"}
    ],
    "size": 15,
    "filters": {
      "genres": ["Action", "RPG"],
      "platforms": ["PC", "PlayStation"],
      "player_perspectives": ["Third person"],
      "rating": {"min_rating": 75}
    }
  }'
```

### Date Range Filtering

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "game",
    "fields": [{"field": "name", "weight": 1}],
    "size": 20,
    "filters": {
      "release_date": {
        "start_date": "2022-01-01",
        "end_date": "2024-12-31"
      }
    }
  }'
```

## ❌ Error Responses

### 400 Bad Request
Missing required field or invalid values:
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "query_text"],
      "msg": "Field required",
      "input": {}
    }
  ],
  "status_code": 422,
  "timestamp": "2024-01-15T10:30:00"
}
```

### 422 Unprocessable Entity
Validation error:
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "size"],
      "msg": "Input should be less than or equal to 100",
      "input": 150
    }
  ],
  "status_code": 422,
  "timestamp": "2024-01-15T10:30:00"
}
```

### 503 Service Unavailable
Elasticsearch connection error:
```json
{
  "detail": "Elasticsearch error: Failed to connect to Elasticsearch at localhost:9200",
  "status_code": 503
}
```

### 500 Internal Server Error
Server error:
```json
{
  "detail": "Internal server error",
  "status_code": 500,
  "timestamp": "2024-01-15T10:30:00"
}
```

## 🔧 Configuration

All configuration is in `config.py`:

```python
# Elasticsearch Connection
ELASTICSEARCH_HOST = "localhost"
ELASTICSEARCH_PORT = 9200
ELASTICSEARCH_INDEX = "games"

# Search Limits
DEFAULT_RESULT_SIZE = 5
MAX_RESULT_SIZE = 100
MIN_RESULT_SIZE = 1

# Searchable Fields
SEARCHABLE_FIELDS = ["name", "summary", "keywords", "themes", "category", "genres"]

# Filterable Fields
FILTERABLE_FIELDS = {
    "genres": "keyword",
    "game_modes": "keyword",
    "platforms": "keyword",
    "player_perspectives": "keyword",
    "themes": "keyword",
    "release_date": "date",
    "rating": "float",
    "aggregated_rating": "float",
}
```

## 📖 Interactive API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing

### Using Curl

Test health check:
```bash
curl http://localhost:8000/health
```
Test get filters:
```bash
curl http://localhost:8000/filters
```
Test search:
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query_text":"test","fields":[{"field":"name"}]}'
```

### Using Python

```python
import requests

# 1. Fetch available filters
filters_response = requests.get("http://localhost:8000/filters")
available_filters = filters_response.json()
print("Available genres:", available_filters['genres'][:5])
print("Available platforms:", available_filters['platforms'][:5])

# 2. Execute search
url = "http://localhost:8000/search"
payload = {
    "query_text": "action",
    "fields": [
        {"field": "name", "weight": 2},
        {"field": "summary"}
    ],
    "size": 10,
    "filters": {
        "genres": ["Action"],
        "platforms": ["PC"]
    }
}

response = requests.post(url, json=payload)
results = response.json()

print(f"Found {results['total']} games in {results['took_ms']}ms")
for game in results['results']:
    print(f"- {game['name']} ({game['aggregated_rating']}%)")
```

## 🔌 Integration with Frontend

The frontend (React) should follow this workflow:

1. **Load Filters on Mount**: GET `/filters` to populate all filter dropdown menus

```javascript
const filtersResponse = await fetch('/filters');
const availableFilters = await filtersResponse.json();
// Use to populate checkboxes/dropdowns for genres, platforms, etc.
```

2. **Build Search Request**: When user searches, build a `SearchRequest` payload with:
   - User's search query
   - Selected fields from a checkbox list
   - Field weights from sliders
   - Filter selections

```javascript
const searchPayload = {
  query_text: userQuery,
  fields: selectedFields.map(f => ({ field: f.name, weight: f.weight })),
  size: resultsPerPage,
  filters: {
    genres: selectedGenres,
    platforms: selectedPlatforms,
    game_modes: selectedGameModes,
    player_perspectives: selectedPerspectives,
    themes: selectedThemes
  }
};
```

3. **Execute Search**: POST to `/search` with the payload

```javascript
const response = await fetch('/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(searchPayload)
});

const data = await response.json();
setResults(data.results);
setTotal(data.total);
setQueryTime(data.took_ms);
```

## 📦 Deployment

### Docker

```bash
docker build -t ir-backend .
docker run -p 8000:8000 -e ELASTICSEARCH_HOST=elasticsearch ir-backend
```

### Environment Variables

```bash
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
```

### Production Checklist

- [ ] Set `ELASTICSEARCH_HOST` to the correct cluster address
- [ ] Use `uvicorn` with multiple workers: `--workers 4`
- [ ] Enable logging for debugging
- [ ] Add CORS middleware if frontend is on different origin
- [ ] Use HTTPS in production
- [ ] Monitor Elasticsearch query performance

## 📄 License

See LICENSE in the repository root.
