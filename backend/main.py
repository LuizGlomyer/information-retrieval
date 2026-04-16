import sys
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError, BadRequestError

from config import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT, ELASTICSEARCH_INDEX
from models.search import SearchRequest, SearchResponse, ErrorResponse
from services.search import SearchService


def validate_elasticsearch_connection() -> Elasticsearch:
    """
    Validate connection to Elasticsearch.
    Exits the application if connection fails.
    """
    es_client = Elasticsearch([f"http://{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}"])
    
    try:
        if not es_client.ping():
            print(f"❌ Failed to connect to Elasticsearch at {ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}")
            sys.exit(1)
        print(f"✓ Connected to Elasticsearch at {ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}")
    except ConnectionError as e:
        print(f"❌ Connection error: {e}")
        sys.exit(1)
    
    return es_client


def validate_index_exists(es_client: Elasticsearch, index_name: str) -> None:
    """
    Validate that the required index exists.
    Exits the application if index doesn't exist.
    """
    try:
        if es_client.indices.exists(index=index_name):
            print(f"✓ Index '{index_name}' exists")
        else:
            print(f"❌ Index '{index_name}' does not exist")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error checking index: {e}")
        sys.exit(1)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    app = FastAPI(
        title="Information Retrieval API",
        version="0.1.0",
        description="Dynamic Elasticsearch search API with weighted field queries and filtering"
    )
    
    # Initialize Elasticsearch client
    es_client = validate_elasticsearch_connection()
    validate_index_exists(es_client, ELASTICSEARCH_INDEX)
    
    # Store client in app state for use in endpoints
    app.state.es_client = es_client
    app.state.games_index = ELASTICSEARCH_INDEX

    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        Health check endpoint.
        
        Returns the status of the API and Elasticsearch connection.
        """
        return {
            "status": "healthy",
            "elasticsearch": "connected",
            "index": ELASTICSEARCH_INDEX
        }

    @app.post(
        "/search",
        response_model=SearchResponse,
        tags=["Search"],
        summary="Dynamic Elasticsearch Search",
        description="Search with weighted fields and optional filtering"
    )
    async def search(request: SearchRequest):
        """
        Execute a dynamic search against the games index.
        
        **Request Body:**
        - `query_text`: (required) Search query string
        - `fields`: (required) List of fields to search with optional weights (default weight: 1)
        - `size`: (optional) Number of results (1-100, default: 5)
        - `filters`: (optional) Filter by category, genres, platforms, themes, date range, rating
        
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
                "category": "main",
                "genres": ["Action", "Adventure"],
                "platforms": ["PC"]
            }
        }
        ```
        
        **Response:**
        - `results`: List of matching games with metadata
        - `total`: Total number of matching documents
        - `took_ms`: Query execution time in milliseconds
        """
        try:
            response = SearchService.execute_search(
                es_client=app.state.es_client,
                index_name=app.state.games_index,
                request=request
            )
            return response

        except (ConnectionError, NotFoundError) as e:
            raise HTTPException(
                status_code=503,
                detail=f"Elasticsearch error: {str(e)}"
            )
        except BadRequestError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid search query: {str(e)}"
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Search error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error: {str(e)}"
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
                "timestamp": datetime.utcnow().isoformat()
            }
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
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return app


# Create app instance at module level for uvicorn
app = create_app()


if __name__ == "__main__":
    print("✓ Application initialized successfully")
    print(f"📚 Index: {ELASTICSEARCH_INDEX}")
    print(f"🌐 Elasticsearch: {ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}")
    print("🚀 To start the server, run: uvicorn main:app --reload --port 8080")
