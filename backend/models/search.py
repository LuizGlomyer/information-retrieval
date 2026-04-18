"""
Pydantic models for search requests and responses.
Provides data validation and type safety for the API.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from config import SEARCHABLE_FIELDS


class SearchField(BaseModel):
    """
    Represents a searchable field with optional weight.
    
    Example:
        {"field": "name", "weight": 2}
        {"field": "summary"}  # weight defaults to 1
    """
    field: str = Field(..., description="Field name to search in (e.g., 'name', 'summary')")
    weight: float = Field(default=1, ge=0.1, le=10, description="Field weight boost (0.1 to 10, default 1)")

    @field_validator("field")
    @classmethod
    def validate_field_is_searchable(cls, v):
        """Ensure the field is in the list of searchable fields."""
        if v not in SEARCHABLE_FIELDS:
            raise ValueError(
                f"Field '{v}' is not searchable. Allowed fields: {', '.join(SEARCHABLE_FIELDS)}"
            )
        return v


class DateRangeFilter(BaseModel):
    """Optional date range for filtering by release_date."""
    start_date: Optional[str] = Field(None, description="Start date in ISO format (e.g., '2020-01-01')")
    end_date: Optional[str] = Field(None, description="End date in ISO format (e.g., '2023-12-31')")


class RatingRangeFilter(BaseModel):
    """Optional rating range for filtering."""
    min_rating: Optional[float] = Field(None, ge=0, le=100, description="Minimum rating")
    max_rating: Optional[float] = Field(None, ge=0, le=100, description="Maximum rating")


class FilterCriteria(BaseModel):
    """
    Optional filtering criteria to narrow down search results.
    All filters are ANDed together.
    Only fields defined here are allowed.
    """
    model_config = ConfigDict(extra='forbid')
    
    genres: Optional[List[str]] = Field(None, description="Filter by any of these genres")
    game_modes: Optional[List[str]] = Field(None, description="Filter by any of these game modes")
    platforms: Optional[List[str]] = Field(None, description="Filter by any of these platforms")
    player_perspectives: Optional[List[str]] = Field(None, description="Filter by any of these player perspectives")
    themes: Optional[List[str]] = Field(None, description="Filter by any of these themes")
    release_date: Optional[DateRangeFilter] = Field(None, description="Filter by release date range")
    rating: Optional[RatingRangeFilter] = Field(None, description="Filter by rating range")
    aggregated_rating: Optional[RatingRangeFilter] = Field(None, description="Filter by aggregated rating range")


class SearchRequest(BaseModel):
    """
    Main request body for dynamic search queries.
    
    Example:
        {
            "query_text": "action adventure",
            "fields": [
                {"field": "name", "weight": 3},
                {"field": "summary", "weight": 1}
            ],
            "size": 10,
            "filters": {
                "genres": ["Action"],
                "platforms": ["PC"]
            }
        }
    """
    query_text: str = Field(..., min_length=1, max_length=500, description="Search query string")
    fields: List[SearchField] = Field(..., min_items=1, description="Fields to search with weights")
    size: int = Field(default=5, ge=1, le=100, description="Number of results to return (1-100)")
    filters: Optional[FilterCriteria] = Field(None, description="Optional filtering criteria")

    @field_validator("fields")
    @classmethod
    def validate_fields_not_empty(cls, v):
        """Ensure at least one field is provided."""
        if not v:
            raise ValueError("At least one field must be provided")
        return v


class GameResult(BaseModel):
    """Represents a single game document returned from search."""
    id: str = Field(..., description="Game ID")
    name: str = Field(..., description="Game name")
    summary: Optional[str] = Field(None, description="Game summary")
    category: Optional[str] = Field(None, description="Game category")
    rating: Optional[float] = Field(None, description="User rating")
    aggregated_rating: Optional[float] = Field(None, description="Aggregated rating")
    genres: Optional[List[str]] = Field(None, description="Genres")
    themes: Optional[List[str]] = Field(None, description="Themes")
    platforms: Optional[List[str]] = Field(None, description="Platforms")
    keywords: Optional[List[str]] = Field(None, description="Keywords")
    release_date: Optional[str] = Field(None, description="Release date")

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    """
    Response body for successful search queries.
    
    Example:
        {
            "results": [
                {"id": "1", "name": "Game Name", ...},
                ...
            ],
            "total": 42,
            "took_ms": 125
        }
    """
    results: List[GameResult] = Field(..., description="Search results")
    total: int = Field(..., ge=0, description="Total number of matching documents")
    took_ms: int = Field(..., ge=0, description="Query execution time in milliseconds")


class ErrorResponse(BaseModel):
    """Response body for error cases."""
    detail: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: str = Field(..., description="ISO timestamp of error")


class FiltersResponse(BaseModel):
    """
    Response body containing all available filter values.
    Each field contains a sorted list of unique values that can be used for filtering.
    
    Example:
        {
            "genres": ["Action", "Adventure", "RPG", "Strategy"],
            "game_modes": ["Single player", "Multiplayer"],
            "platforms": ["PC", "PlayStation", "Xbox"],
            "player_perspectives": ["First person", "Third person"],
            "themes": ["Fantasy", "Sci-Fi", "Historical"]
        }
    """
    genres: List[str] = Field(..., description="All available genres")
    game_modes: List[str] = Field(..., description="All available game modes")
    platforms: List[str] = Field(..., description="All available platforms")
    player_perspectives: List[str] = Field(..., description="All available player perspectives")
    themes: List[str] = Field(..., description="All available themes")
