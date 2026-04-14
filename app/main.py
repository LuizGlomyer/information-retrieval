import sys
from fastapi import FastAPI
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError

# Configuration
ELASTICSEARCH_HOST = "localhost"
ELASTICSEARCH_PORT = 9200
GAMES_INDEX = "games"


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
    app = FastAPI(title="Information Retrieval API", version="0.1.0")
    
    # Initialize Elasticsearch client
    es_client = validate_elasticsearch_connection()
    validate_index_exists(es_client, GAMES_INDEX)
    
    # Store client in app state for use in endpoints
    app.state.es_client = es_client
    app.state.games_index = GAMES_INDEX
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "elasticsearch": "connected",
            "index": GAMES_INDEX
        }
    
    return app


# Create app instance at module level for uvicorn
app = create_app()


if __name__ == "__main__":
    print("✓ Application initialized successfully")
    # To run: uvicorn app.main:app --reload
