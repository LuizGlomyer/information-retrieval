import sys
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError

from config import (
    ELASTICSEARCH_HOST,
    ELASTICSEARCH_PORT,
    BM25_INDEX_NAME,
    SVM_INDEX_NAME,
)
from services.index_manager import IndexManager
from routes import router


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
    app.include_router(router)

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
