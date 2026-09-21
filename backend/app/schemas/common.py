"""
Common response schemas used across multiple API endpoints.
"""
from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Wrapper for successful API responses."""
    success: bool = True
    data: T
    message: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Wrapper for paginated list responses."""
    success: bool = True
    data: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorDetail(BaseModel):
    """A single validation error detail."""
    field: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error response format."""
    success: bool = False
    error: dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    database: bool
    environment: str
