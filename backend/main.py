import sys
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
    Bm25IdNameSearchRequest,
    MultiAlgorithmSearchResponse,
    Bm25IdNameSearchResponse,
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
        description="Multi-algorithm search API: BM25 + TF-IDF (SVM) with config-driven field weights and filtering",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8090", "http://127.0.0.1:8090"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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
        - `size`: (optional) Number of results per algorithm (1-1000, default: 5)
        - `explain`: (optional) If true, include per-hit score explanations in each algorithm result
        - `metrics`: (optional) If true, include IR metrics per algorithm (ranx);
          uses ``qrels.QUERY_QRELS`` when ``query_text.strip()`` matches a key, otherwise all metrics are zero.
          ``*_at_5`` (including ``f1_at_5``) when ``size >= 5``; ``*_at_10`` (including ``f1_at_10``) when ``size >= 10``
        - `filters`: (optional) Filter by genres, game_modes, platforms, player_perspectives, themes, date range, rating

        Multi-match fields and boosts are defined in ``config.DEFAULT_SEARCH_FIELD_WEIGHTS`` (not sent by the client).

        **Example Request:**
        ```json
        {
            "query_text": "action adventure",
            "size": 10,
            "explain": false,
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

        - `bm25`: Results from Elasticsearch BM25 probabilistic ranking (field weights from server config)
        - `svm`: Results from Elasticsearch TF-IDF Vector Space Model (Scripted Similarity; same query body and weights as BM25)
        - `results`: Ranked games with score, rank, and algorithm metadata
        - `total`: Total matching documents across all filters
        - `execution_time_ms`: Query execution time for each algorithm in milliseconds
        - `metrics`: When ``metrics`` was true, each algorithm block includes ``precision_at_1``,
          ``ndcg_at_1``, ``recall_at_1``, ``mean_average_precision``; ``*_at_5`` when ``size >= 5``;
          ``*_at_10`` and ``f1_at_10`` when ``size >= 10`` (omitted otherwise)
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

    @app.post(
        "/search/bm25-resumed",
        response_model=Bm25IdNameSearchResponse,
        response_model_exclude_none=True,
        tags=["Search"],
        summary="BM25 resumed search (id, name, optional platforms)",
        description="BM25-ranked search returning game id and name, and optionally platforms per hit when name_only is false.",
    )
    async def search_bm25_id_name(request: Bm25IdNameSearchRequest):
        """
        Execute a BM25 search and return ``id`` and ``name`` for each hit by default.

        If ``name_only`` is false, results also include ``platforms``.
        Uses the same request body fields as ``POST /search`` plus ``name_only``.
        ``explain`` and ``metrics`` are ignored on this endpoint.
        """
        try:
            return SearchService.execute_bm25_id_name_search(
                es_client=app.state.es_client, request=request
            )

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
