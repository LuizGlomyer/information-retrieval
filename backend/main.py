import sys
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError, BadRequestError

from config import (
    ELASTICSEARCH_HOST,
    ELASTICSEARCH_PORT,
    BM25_INDEX_NAME,
    SVM_INDEX_NAME,
)
from models.search import (
    SearchRequest,
    MultiAlgorithmSearchResponse,
    FiltersResponse,
)
from services.search import SearchService
from services.filters import FiltersService
from services.index_manager import IndexManager


def validate_elasticsearch_connection() -> Elasticsearch:
    """
    Validate connection to Elasticsearch.
    Exits the application if connection fails.
    """
    es_client = Elasticsearch([f"http://{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}"])

    try:
        if not es_client.ping():
            print(
                f"❌ Failed to connect to Elasticsearch at {ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}"
            )
            sys.exit(1)
        print(
            f"✓ Connected to Elasticsearch at {ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}"
        )
    except ConnectionError as e:
        print(f"❌ Connection error: {e}")
        sys.exit(1)

    return es_client


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    Initializes both BM25 and SVM (TF-IDF) indices for multi-algorithm search.
    """
    app = FastAPI(
        title="Information Retrieval API",
        version="0.2.0",
        description="Multi-algorithm search API: BM25 + TF-IDF (SVM) with weighted fields and filtering",
    )

    # Initialize Elasticsearch client
    es_client = validate_elasticsearch_connection()

    # Initialize both indices (BM25 and SVM)
    indices_ok = IndexManager.initialize_indices(es_client)
    if not indices_ok:
        print("⚠ Warning: Failed to initialize some indices")

    # Store client in app state for use in endpoints
    app.state.es_client = es_client

    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        Health check endpoint.

        Returns the status of the API and Elasticsearch connection.
        """
        return {
            "status": "healthy",
            "elasticsearch": "connected",
            "indices": {"bm25": BM25_INDEX_NAME, "svm": SVM_INDEX_NAME},
        }

    @app.post(
        "/search",
        response_model=MultiAlgorithmSearchResponse,
        tags=["Search"],
        summary="Multi-Algorithm Search (BM25 + SVM)",
        description="Search with BM25 and SVM ranking algorithms",
    )
    async def search(request: SearchRequest):
        """
        Execute a multi-algorithm search against the games index.

        Returns results from both **BM25** (Elasticsearch native similarity) and **SVM** (TF-IDF Vector Space Model)
        ranking algorithms. Both algorithms apply the same filters. Results are sorted by score
        within each algorithm (highest scores first).

        **Implementation Details:**
        - **BM25**: Elasticsearch's default probabilistic ranking function on `games` index
        - **SVM**: TF-IDF (Salton 1971) calculated via Elasticsearch Scripted Similarity on `games_svm` index
          - Formula: `score = query.boost × √(freq) × idf × (1/√(length))`
          - Computed directly in Elasticsearch during query execution

        **Request Body:**
        - `query_text`: (required) Search query string
        - `fields`: (required) List of fields to search with optional weights (default weight: 1)
        - `size`: (optional) Number of results per algorithm (1-100, default: 5)
        - `filters`: (optional) Filter by genres, game_modes, platforms, player_perspectives, themes, date range, rating

        **Example Request:**
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
                "platforms": ["PC"]
            }
        }
        ```

        **Response:**
        Contains results from both algorithms:
        ```json
        {
            "bm25": {
                "results": [
                    {
                        "id": "1",
                        "name": "Game Name",
                        "score": 9.5,
                        "rank": 1,
                        "algorithm": "bm25",
                        "summary": "...",
                        ...
                    }
                ],
                "total": 42,
                "execution_time_ms": 120
            },
            "svm": {
                "results": [...],
                "total": 42,
                "execution_time_ms": 45
            }
        }
        ```

        - `bm25`: Results from Elasticsearch BM25 probabilistic ranking with field-weighted scoring
        - `svm`: Results from Elasticsearch TF-IDF Vector Space Model (Scripted Similarity) with field-weighted scoring
        - `results`: Ranked games with score, rank, and algorithm metadata
        - `total`: Total matching documents across all filters
        - `execution_time_ms`: Query execution time for each algorithm in milliseconds
        """
        try:
            response = SearchService.execute_search(
                es_client=app.state.es_client, request=request
            )
            return response

        except (ConnectionError, NotFoundError) as e:
            raise HTTPException(
                status_code=503, detail=f"Elasticsearch error: {str(e)}"
            )
        except BadRequestError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid search query: {str(e)}"
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Search error: {str(e)}")
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {str(e)}"
            )

    @app.get(
        "/filters",
        response_model=FiltersResponse,
        tags=["Filters"],
        summary="Get Available Filter Values",
        description="Retrieve all available filter values for the frontend",
    )
    async def get_filters():
        """
        Get all available filter values for genres, game_modes, platforms, player_perspectives, and themes.

        This endpoint returns all unique values from each filter field in the index.
        These values can be used to populate dropdown menus or filter selections in the frontend.

        **Response:**
        ```json
        {
            "genres": ["Action", "Adventure", "RPG", ...],
            "game_modes": ["Single player", "Multiplayer", ...],
            "platforms": ["PC", "PlayStation", "Xbox", ...],
            "player_perspectives": ["First person", "Third person", ...],
            "themes": ["Fantasy", "Sci-Fi", "Horror", ...]
        }
        ```
        """
        try:
            filters_data = FiltersService.get_all_filters(
                es_client=app.state.es_client, index_name=app.state.games_index
            )

            # Convert dict to FiltersResponse model
            return FiltersResponse(**filters_data)

        except (ConnectionError, NotFoundError) as e:
            raise HTTPException(
                status_code=503, detail=f"Elasticsearch error: {str(e)}"
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to fetch filters: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Internal server error: {str(e)}"
            )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request, exc):
        """
        Handle Pydantic validation errors.
        Returns 422 with detailed validation error information.
        """
        return JSONResponse(
            status_code=422,
            content={
                "detail": exc.errors(),
                "status_code": 422,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        """
        Handle unexpected errors.
        """
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "status_code": 500,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    return app


# Create app instance at module level for uvicorn
app = create_app()


if __name__ == "__main__":
    print("✓ Application initialized successfully")
    print(f"📚 BM25 Index: {BM25_INDEX_NAME}")
    print(f"📚 SVM Index: {SVM_INDEX_NAME}")
    print(f"🌐 Elasticsearch: {ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}")
    print("🚀 To start the server, run: uvicorn main:app --reload --port 8080")
