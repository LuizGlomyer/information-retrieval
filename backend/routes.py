from fastapi import APIRouter, HTTPException, Request
from elasticsearch.exceptions import ConnectionError, NotFoundError, BadRequestError

from config import BM25_INDEX_NAME, SVM_INDEX_NAME
from models.search import (
    SearchRequest,
    Bm25IdNameSearchRequest,
    MultiAlgorithmSearchResponse,
    Bm25IdNameSearchResponse,
    FiltersResponse,
)
from services.search import SearchService
from services.filters import FiltersService

router = APIRouter()


@router.get("/health", tags=["Health"])
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


@router.post(
    "/search",
    response_model=MultiAlgorithmSearchResponse,
    tags=["Search"],
    summary="Multi-Algorithm Search (BM25 + SVM)",
    description="Search with BM25 and SVM ranking algorithms",
)
async def search(request: SearchRequest, app_request: Request):
    """
    Execute a multi-algorithm search against the games index.

    Returns results from both **BM25** (Elasticsearch native similarity) and **SVM** (TF-IDF Vector Space Model)
    ranking algorithms. Both algorithms apply the same filters. Results are sorted by score
    within each algorithm (highest scores first).
    """
    try:
        response = SearchService.execute_search(
            es_client=app_request.app.state.es_client, request=request
        )
        return response

    except (ConnectionError, NotFoundError) as e:
        raise HTTPException(status_code=503, detail=f"Elasticsearch error: {str(e)}")
    except BadRequestError as e:
        raise HTTPException(status_code=400, detail=f"Invalid search query: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Search error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/search/bm25-resumed",
    response_model=Bm25IdNameSearchResponse,
    response_model_exclude_none=True,
    tags=["Search"],
    summary="BM25 resumed search (id, name, optional platforms, optional hybrid)",
    description=(
        "BM25-ranked search returning game id and name, and optionally platforms per hit when name_only is false. "
        "If hybrid is true, BM25 hybrid ranking is used instead of plain BM25."
    ),
)
async def search_bm25_id_name(request: Bm25IdNameSearchRequest, app_request: Request):
    """
    Execute a BM25 or BM25 hybrid search and return ``id`` and ``name`` for each hit by default.

    If ``name_only`` is false, results also include ``platforms``.
    Uses the same request body fields as ``POST /search`` plus ``name_only`` and ``hybrid``.
    ``explain`` and ``metrics`` are ignored on this endpoint.
    """
    try:
        return SearchService.execute_bm25_id_name_search(
            es_client=app_request.app.state.es_client, request=request
        )

    except (ConnectionError, NotFoundError) as e:
        raise HTTPException(status_code=503, detail=f"Elasticsearch error: {str(e)}")
    except BadRequestError as e:
        raise HTTPException(status_code=400, detail=f"Invalid search query: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Search error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/filters",
    response_model=FiltersResponse,
    tags=["Filters"],
    summary="Get Available Filter Values",
    description="Retrieve all available filter values for the frontend",
)
async def get_filters(app_request: Request):
    """
    Get all available filter values for genres, game_modes, platforms, player_perspectives, and themes.

    This endpoint returns all unique values from each filter field in the index.
    These values can be used to populate dropdown menus or filter selections in the frontend.
    """
    try:
        filters_data = FiltersService.get_all_filters(
            es_client=app_request.app.state.es_client,
            index_name=BM25_INDEX_NAME,
        )

        return FiltersResponse(**filters_data)

    except (ConnectionError, NotFoundError) as e:
        raise HTTPException(status_code=503, detail=f"Elasticsearch error: {str(e)}")
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to fetch filters: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
