"""Tests for pagination functionality."""

from typing import Any

import pytest
from pydantic import ValidationError

from enrichmcp.pagination import (
    CursorParams,
    CursorResult,
    PageResult,
    PaginatedResult,
    PaginationParams,
)


class TestPaginationParams:
    """Test pagination parameter handling."""

    def test_default_params(self):
        """Test default pagination parameters."""
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 50
        assert params.order_direction == "asc"
        assert params.order_by is None

    def test_custom_params(self):
        """Test custom pagination parameters."""
        params = PaginationParams(
            page=2, page_size=25, order_by="created_at", order_direction="desc"
        )
        assert params.page == 2
        assert params.page_size == 25
        assert params.order_by == "created_at"
        assert params.order_direction == "desc"

    def test_offset_calculation(self):
        """Test SQL offset calculation."""
        params = PaginationParams(page=1, page_size=10)
        assert params.get_offset() == 0

        params = PaginationParams(page=3, page_size=10)
        assert params.get_offset() == 20

        params = PaginationParams(page=5, page_size=15)
        assert params.get_offset() == 60

    def test_limit_calculation(self):
        """Test SQL limit calculation."""
        params = PaginationParams(page=1, page_size=10)
        assert params.get_limit() == 10

        params = PaginationParams(page=3, page_size=25)
        assert params.get_limit() == 25

    def test_validation_page_min(self):
        """Test page validation - minimum value."""
        with pytest.raises(ValidationError):
            PaginationParams(page=0)

    def test_validation_page_size_min(self):
        """Test page_size validation - minimum value."""
        with pytest.raises(ValidationError):
            PaginationParams(page_size=0)

    def test_validation_page_size_max(self):
        """Test page_size validation - maximum value."""
        with pytest.raises(ValidationError):
            PaginationParams(page_size=1001)

    def test_edge_case_values(self):
        """Test edge case values."""
        # Minimum valid values
        params = PaginationParams(page=1, page_size=1)
        assert params.page == 1
        assert params.page_size == 1
        assert params.get_offset() == 0

        # Maximum valid page_size
        params = PaginationParams(page=1, page_size=1000)
        assert params.page_size == 1000


class TestCursorParams:
    """Test cursor parameter handling."""

    def test_default_params(self):
        """Test default cursor parameters."""
        params = CursorParams()
        assert params.cursor is None
        assert params.page_size == 50
        assert params.order_direction == "asc"
        assert params.order_by is None

    def test_custom_params(self):
        """Test custom cursor parameters."""
        params = CursorParams(cursor="abc123", page_size=25, order_by="id", order_direction="desc")
        assert params.cursor == "abc123"
        assert params.page_size == 25
        assert params.order_by == "id"
        assert params.order_direction == "desc"

    def test_validation_page_size_min(self):
        """Test page_size validation - minimum value."""
        with pytest.raises(ValidationError):
            CursorParams(page_size=0)

    def test_validation_page_size_max(self):
        """Test page_size validation - maximum value."""
        with pytest.raises(ValidationError):
            CursorParams(page_size=1001)


class TestPageResult:
    """Test page-based pagination results."""

    def test_create_first_page(self):
        """Test creating first page of results."""
        items = [1, 2, 3, 4, 5]
        result = PageResult.create(items=items, page=1, page_size=5, has_next=True, total_items=15)

        assert result.items == items
        assert result.page == 1
        assert result.page_size == 5
        assert result.has_next is True
        assert result.total_items == 15
        assert result.total_pages == 3
        assert result.has_previous is False

    def test_create_middle_page(self):
        """Test creating middle page of results."""
        items = [6, 7, 8, 9, 10]
        result = PageResult.create(items=items, page=2, page_size=5, has_next=True, total_items=15)

        assert result.items == items
        assert result.page == 2
        assert result.page_size == 5
        assert result.has_next is True
        assert result.has_previous is True

    def test_create_last_page(self):
        """Test creating last page of results."""
        items = [11, 12, 13, 14, 15]
        result = PageResult.create(items=items, page=3, page_size=5, has_next=False, total_items=15)

        assert result.items == items
        assert result.page == 3
        assert result.has_next is False
        assert result.has_previous is True
        assert result.total_pages == 3

    def test_create_without_total(self):
        """Test creating page result without total count."""
        items = [1, 2, 3]
        result = PageResult.create(items=items, page=1, page_size=3, has_next=True)

        assert result.items == items
        assert result.page == 1
        assert result.has_next is True
        assert result.total_items is None
        assert result.total_pages is None

    def test_empty_results(self):
        """Test page result with no items."""
        result = PageResult.create(items=[], page=1, page_size=10, has_next=False, total_items=0)

        assert result.items == []
        assert result.page == 1
        assert result.has_next is False
        assert result.has_previous is False
        assert result.total_items == 0
        assert result.total_pages == 0

    def test_get_next_params(self):
        """Test getting parameters for next page."""
        result = PageResult.create(items=[1, 2, 3], page=2, page_size=10, has_next=True)

        next_params = result.get_next_params()
        assert next_params == {"page": 3, "page_size": 10}

    def test_total_pages_calculation(self):
        """Test total pages calculation with various scenarios."""
        # Exact division
        result = PageResult.create([], 1, 10, False, total_items=20)
        assert result.total_pages == 2

        # With remainder
        result = PageResult.create([], 1, 10, False, total_items=25)
        assert result.total_pages == 3

        # Single page
        result = PageResult.create([], 1, 10, False, total_items=5)
        assert result.total_pages == 1

        # Zero items
        result = PageResult.create([], 1, 10, False, total_items=0)
        assert result.total_pages == 0

    def test_protocol_compliance(self):
        """Test that PageResult implements PaginatedResult protocol."""
        result = PageResult.create([1, 2, 3], 1, 10, True)

        # Should satisfy protocol
        assert isinstance(result, PaginatedResult)
        assert hasattr(result, "items")
        assert hasattr(result, "page_size")
        assert hasattr(result, "has_next")
        assert hasattr(result, "get_next_params")

    def test_validation_page_min(self):
        """Test page validation."""
        with pytest.raises(ValidationError):
            PageResult(items=[], page=0, page_size=10, has_next=False)

    def test_validation_page_size_min(self):
        """Test page_size validation."""
        with pytest.raises(ValidationError):
            PageResult(items=[], page=1, page_size=0, has_next=False)

    def test_validation_total_items_min(self):
        """Test total_items validation."""
        with pytest.raises(ValidationError):
            PageResult(items=[], page=1, page_size=10, has_next=False, total_items=-1)


class TestCursorResult:
    """Test cursor-based pagination results."""

    def test_create_with_cursor(self):
        """Test creating cursor result with next cursor."""
        items = [1, 2, 3, 4, 5]
        result = CursorResult.create(items=items, next_cursor="abc123", page_size=5)

        assert result.items == items
        assert result.next_cursor == "abc123"
        assert result.page_size == 5
        assert result.has_next is True

    def test_create_without_cursor(self):
        """Test creating cursor result without next cursor (last page)."""
        items = [1, 2, 3]
        result = CursorResult.create(items=items, next_cursor=None, page_size=5)

        assert result.items == items
        assert result.next_cursor is None
        assert result.page_size == 5
        assert result.has_next is False

    def test_empty_results(self):
        """Test cursor result with no items."""
        result = CursorResult.create(items=[], next_cursor=None, page_size=10)

        assert result.items == []
        assert result.next_cursor is None
        assert result.has_next is False

    def test_get_next_params(self):
        """Test getting parameters for next page."""
        result = CursorResult.create(items=[1, 2, 3], next_cursor="xyz789", page_size=10)

        next_params = result.get_next_params()
        assert next_params == {"cursor": "xyz789", "page_size": 10}

    def test_get_next_params_no_cursor(self):
        """Test getting next params when no cursor available."""
        result = CursorResult.create(items=[1, 2, 3], next_cursor=None, page_size=10)

        next_params = result.get_next_params()
        assert next_params == {"cursor": None, "page_size": 10}

    def test_protocol_compliance(self):
        """Test that CursorResult implements PaginatedResult protocol."""
        result = CursorResult.create([1, 2, 3], "cursor123", 10)

        # Should satisfy protocol
        assert isinstance(result, PaginatedResult)
        assert hasattr(result, "items")
        assert hasattr(result, "page_size")
        assert hasattr(result, "has_next")
        assert hasattr(result, "get_next_params")

    def test_validation_page_size_min(self):
        """Test page_size validation."""
        with pytest.raises(ValidationError):
            CursorResult(items=[], next_cursor=None, page_size=0)


class TestProtocolUsage:
    """Test usage of the PaginatedResult protocol."""

    def test_protocol_with_page_result(self):
        """Test protocol works with PageResult."""
        result: PaginatedResult[int] = PageResult.create([1, 2, 3], 1, 10, True)

        assert len(result.items) == 3
        assert result.page_size == 10
        assert result.has_next is True

        next_params = result.get_next_params()
        assert "page" in next_params

    def test_protocol_with_cursor_result(self):
        """Test protocol works with CursorResult."""
        result: PaginatedResult[int] = CursorResult.create([1, 2, 3], "cursor", 10)

        assert len(result.items) == 3
        assert result.page_size == 10
        assert result.has_next is True

        next_params = result.get_next_params()
        assert "cursor" in next_params

    def test_generic_handling(self):
        """Test generic handling of paginated results."""

        def process_paginated_result(result: PaginatedResult[int]) -> dict[str, Any]:
            """Generic function that works with any paginated result."""
            return {
                "item_count": len(result.items),
                "page_size": result.page_size,
                "has_more": result.has_next,
                "next_params": result.get_next_params(),
            }

        # Test with PageResult
        page_result = PageResult.create([1, 2, 3], 1, 10, True)
        page_info = process_paginated_result(page_result)
        assert page_info["item_count"] == 3
        assert page_info["next_params"]["page"] == 2

        # Test with CursorResult
        cursor_result = CursorResult.create([4, 5, 6], "next_cursor", 10)
        cursor_info = process_paginated_result(cursor_result)
        assert cursor_info["item_count"] == 3
        assert cursor_info["next_params"]["cursor"] == "next_cursor"
