"""
Pagination support for enrichmcp.

Provides pagination result types and utilities for handling paginated data
in MCP resources and relationship resolvers.
"""

from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel, Field

T = TypeVar("T")


@runtime_checkable
class PaginatedResult(Protocol, Generic[T]):
    """Protocol for paginated results."""

    items: list[T]
    page_size: int
    has_next: bool

    def get_next_params(self) -> dict[str, Any]:
        """Get parameters needed to fetch the next page."""
        ...


class PageResult(BaseModel, Generic[T]):
    """Page-number based pagination result."""

    items: list[T] = Field(description="Items for current page")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, description="Items per page")
    has_next: bool = Field(description="Whether there are more pages")
    total_items: int | None = Field(None, ge=0, description="Total items (if known)")

    @property
    def has_previous(self) -> bool:
        """Whether there are previous pages."""
        return self.page > 1

    @property
    def total_pages(self) -> int | None:
        """Total number of pages (if total_items is known)."""
        if self.total_items is None:
            return None
        return (self.total_items + self.page_size - 1) // self.page_size

    def get_next_params(self) -> dict[str, Any]:
        """Get parameters for fetching the next page."""
        return {"page": self.page + 1, "page_size": self.page_size}

    @classmethod
    def create(
        cls,
        items: list[T],
        page: int,
        page_size: int,
        has_next: bool,
        total_items: int | None = None,
    ) -> "PageResult[T]":
        """Create a page result with the given parameters."""
        return cls(
            items=items,
            page=page,
            page_size=page_size,
            has_next=has_next,
            total_items=total_items,
        )


class CursorResult(BaseModel, Generic[T]):
    """Cursor-based pagination result."""

    items: list[T] = Field(description="Items for current page")
    next_cursor: str | None = Field(None, description="Cursor for next page")
    page_size: int = Field(ge=1, description="Items per page")

    @property
    def has_next(self) -> bool:
        """Whether there are more pages."""
        return self.next_cursor is not None

    def get_next_params(self) -> dict[str, Any]:
        """Get parameters for fetching the next page."""
        return {"cursor": self.next_cursor, "page_size": self.page_size}

    @classmethod
    def create(
        cls,
        items: list[T],
        next_cursor: str | None,
        page_size: int,
    ) -> "CursorResult[T]":
        """Create a cursor result with the given parameters."""
        return cls(
            items=items,
            next_cursor=next_cursor,
            page_size=page_size,
        )


class PaginationParams(BaseModel):
    """Standard pagination parameters for page-based pagination."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=50, ge=1, le=1000, description="Items per page")
    order_by: str | None = Field(None, description="Field to order by")
    order_direction: str = Field(default="asc", description="Order direction: asc or desc")

    def get_offset(self) -> int:
        """Calculate SQL OFFSET value."""
        return (self.page - 1) * self.page_size

    def get_limit(self) -> int:
        """Get SQL LIMIT value."""
        return self.page_size


class CursorParams(BaseModel):
    """Standard parameters for cursor-based pagination."""

    cursor: str | None = Field(None, description="Cursor for pagination")
    page_size: int = Field(default=50, ge=1, le=1000, description="Items per page")
    order_by: str | None = Field(None, description="Field to order by")
    order_direction: str = Field(default="asc", description="Order direction: asc or desc")
