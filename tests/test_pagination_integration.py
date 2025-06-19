"""Integration tests for pagination with resources and relationships."""

from datetime import datetime
from unittest.mock import Mock

import pytest
from pydantic import Field

from enrichmcp import (
    CursorParams,
    CursorResult,
    EnrichContext,
    EnrichMCP,
    EnrichModel,
    PageResult,
    PaginationParams,
    Relationship,
)


@pytest.fixture
def app():
    """Create test app with entities."""
    app = EnrichMCP(title="Test API", description="Test API")

    # Define entities with forward references like in SQLite example
    @app.entity
    class User(EnrichModel):
        """Test user model."""

        id: int = Field(description="User ID")
        name: str = Field(description="User name")
        created_at: datetime = Field(description="Creation timestamp")

        # Relationships - using different types for different tests
        orders: list["Order"] = Relationship(description="User orders")
        orders_paginated: PageResult["Order"] = Relationship(
            description="User orders with pagination"
        )
        orders_cursor: CursorResult["Order"] = Relationship(description="User orders with cursor")

    @app.entity
    class Order(EnrichModel):
        """Test order model."""

        id: int = Field(description="Order ID")
        user_id: int = Field(description="User ID")
        total: float = Field(description="Order total")
        created_at: datetime = Field(description="Creation timestamp")

        # Reference to User
        user: User = Relationship(description="Order user")

    # Store entities on app for test access
    app._test_user = User
    app._test_order = Order

    # Rebuild models after all entities are defined
    User.model_rebuild()
    Order.model_rebuild()

    return app


@pytest.fixture
def mock_context():
    """Create mock context."""
    ctx = Mock(spec=EnrichContext)
    ctx.request_context = Mock()
    ctx.request_context.lifespan_context = {"db": Mock()}
    return ctx


@pytest.fixture
def sample_users(app):
    """Create sample users for testing."""
    user_cls = app._test_user
    return [
        user_cls(id=i, name=f"User {i}", created_at=datetime(2023, 1, (i % 31) + 1))
        for i in range(1, 101)  # 100 users
    ]


@pytest.fixture
def sample_orders(app):
    """Create sample orders for testing."""
    order_cls = app._test_order
    return [
        order_cls(
            id=i,
            user_id=(i % 10) + 1,  # Distribute orders among first 10 users
            total=float(i * 10),
            created_at=datetime(2023, 1, i % 30 + 1),
        )
        for i in range(1, 51)  # 50 orders
    ]


class TestPaginatedResources:
    """Test pagination with resource functions."""

    @pytest.mark.asyncio
    async def test_page_based_resource(self, app, mock_context, sample_users):
        """Test page-based pagination in resource."""
        user_cls = app._test_user

        @app.retrieve
        async def list_users(
            ctx: EnrichContext, page: int = 1, page_size: int = 10
        ) -> PageResult[user_cls]:
            """List users with page-based pagination."""
            # Simulate database pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size

            page_users = sample_users[start_idx:end_idx]
            has_next = end_idx < len(sample_users)

            return PageResult.create(
                items=page_users,
                page=page,
                page_size=page_size,
                has_next=has_next,
                total_items=len(sample_users),
            )

        # Test first page
        result = await list_users(ctx=mock_context, page=1, page_size=10)

        assert isinstance(result, PageResult)
        assert len(result.items) == 10
        assert result.page == 1
        assert result.page_size == 10
        assert result.has_next is True
        assert result.has_previous is False
        assert result.total_items == 100
        assert result.total_pages == 10

        # Verify first page items
        assert result.items[0].id == 1
        assert result.items[9].id == 10

        # Test middle page
        result = await list_users(ctx=mock_context, page=5, page_size=10)

        assert result.page == 5
        assert result.has_next is True
        assert result.has_previous is True
        assert result.items[0].id == 41
        assert result.items[9].id == 50

        # Test last page
        result = await list_users(ctx=mock_context, page=10, page_size=10)

        assert result.page == 10
        assert result.has_next is False
        assert result.has_previous is True
        assert result.items[0].id == 91
        assert result.items[9].id == 100

    @pytest.mark.asyncio
    async def test_cursor_based_resource(self, app, mock_context, sample_users):
        """Test cursor-based pagination in resource."""
        user_cls = app._test_user

        @app.retrieve
        async def list_users_cursor(
            ctx: EnrichContext, cursor: str | None = None, page_size: int = 10
        ) -> CursorResult[user_cls]:
            """List users with cursor-based pagination."""
            # Simulate cursor-based pagination
            start_idx = 0 if cursor is None else int(cursor)
            end_idx = start_idx + page_size

            page_users = sample_users[start_idx:end_idx]
            next_cursor = str(end_idx) if end_idx < len(sample_users) else None

            return CursorResult.create(
                items=page_users, next_cursor=next_cursor, page_size=page_size
            )

        # Test first page (no cursor)
        result = await list_users_cursor(ctx=mock_context, cursor=None, page_size=10)

        assert isinstance(result, CursorResult)
        assert len(result.items) == 10
        assert result.page_size == 10
        assert result.has_next is True
        assert result.next_cursor == "10"

        # Verify first page items
        assert result.items[0].id == 1
        assert result.items[9].id == 10

        # Test second page using cursor
        result = await list_users_cursor(ctx=mock_context, cursor="10", page_size=10)

        assert len(result.items) == 10
        assert result.has_next is True
        assert result.next_cursor == "20"
        assert result.items[0].id == 11
        assert result.items[9].id == 20

        # Test last page
        result = await list_users_cursor(ctx=mock_context, cursor="90", page_size=10)

        assert len(result.items) == 10
        assert result.has_next is False
        assert result.next_cursor is None
        assert result.items[0].id == 91
        assert result.items[9].id == 100

    @pytest.mark.asyncio
    async def test_pagination_with_filtering(self, app, mock_context, sample_users):
        """Test pagination combined with filtering."""
        user_cls = app._test_user

        @app.retrieve
        async def search_users(
            ctx: EnrichContext, name_contains: str, page: int = 1, page_size: int = 5
        ) -> PageResult[user_cls]:
            """Search users with pagination."""
            # Filter users by name
            filtered_users = [
                user for user in sample_users if name_contains.lower() in user.name.lower()
            ]

            # Apply pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size

            page_users = filtered_users[start_idx:end_idx]
            has_next = end_idx < len(filtered_users)

            return PageResult.create(
                items=page_users,
                page=page,
                page_size=page_size,
                has_next=has_next,
                total_items=len(filtered_users),
            )

        # Search for users containing "1" (User 1, User 10, User 11, etc.)
        result = await search_users(ctx=mock_context, name_contains="1", page=1, page_size=5)

        assert isinstance(result, PageResult)
        assert len(result.items) == 5
        assert result.page == 1
        assert result.has_next is True

        # Verify filtering worked
        for user in result.items:
            assert "1" in user.name

    @pytest.mark.asyncio
    async def test_empty_page_result(self, app, mock_context):
        """Test pagination with no results."""
        user_cls = app._test_user

        @app.retrieve
        async def list_empty_users(
            ctx: EnrichContext, page: int = 1, page_size: int = 10
        ) -> PageResult[user_cls]:
            """List users that returns empty results."""
            return PageResult.create(
                items=[], page=page, page_size=page_size, has_next=False, total_items=0
            )

        result = await list_empty_users(ctx=mock_context, page=1, page_size=10)

        assert isinstance(result, PageResult)
        assert len(result.items) == 0
        assert result.page == 1
        assert result.has_next is False
        assert result.has_previous is False
        assert result.total_items == 0
        assert result.total_pages == 0


class TestPaginatedRelationships:
    """Test pagination with relationship resolvers."""

    @pytest.mark.asyncio
    async def test_paginated_one_to_many_relationship(self, app, mock_context, sample_orders):
        """Test paginated one-to-many relationship resolver."""
        user_cls = app._test_user

        @user_cls.orders_paginated.resolver
        async def get_user_orders(
            user_id: int, ctx: EnrichContext, page: int = 1, page_size: int = 5
        ) -> PageResult["Order"]:  # noqa: F821
            """Get user orders with pagination."""
            # Filter orders for the user
            user_orders = [order for order in sample_orders if order.user_id == user_id]

            # Apply pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size

            page_orders = user_orders[start_idx:end_idx]
            has_next = end_idx < len(user_orders)

            return PageResult.create(
                items=page_orders,
                page=page,
                page_size=page_size,
                has_next=has_next,
                total_items=len(user_orders),
            )

        # Test getting orders for user 1 (should have 5 orders: 1, 11, 21, 31, 41)
        result = await get_user_orders(user_id=1, ctx=mock_context, page=1, page_size=3)

        assert isinstance(result, PageResult)
        assert len(result.items) == 3
        assert result.page == 1
        assert result.has_next is True
        assert result.total_items == 5

        # Verify orders belong to correct user
        for order in result.items:
            assert order.user_id == 1

        # Test second page
        result = await get_user_orders(user_id=1, ctx=mock_context, page=2, page_size=3)

        assert len(result.items) == 2  # Remaining orders
        assert result.page == 2
        assert result.has_next is False
        assert result.has_previous is True

    @pytest.mark.asyncio
    async def test_paginated_relationship_with_cursor(self, app, mock_context, sample_orders):
        """Test cursor-based pagination in relationship resolver."""
        user_cls = app._test_user

        @user_cls.orders_cursor.resolver
        async def get_user_orders_cursor(
            user_id: int,
            ctx: EnrichContext,
            cursor: str | None = None,
            page_size: int = 3,
        ) -> CursorResult["Order"]:  # noqa: F821
            """Get user orders with cursor pagination."""
            user_orders = [order for order in sample_orders if order.user_id == user_id]

            # Sort by ID for consistent cursor behavior
            user_orders.sort(key=lambda x: x.id)

            # Apply cursor pagination
            start_idx = 0 if cursor is None else int(cursor)
            end_idx = start_idx + page_size

            page_orders = user_orders[start_idx:end_idx]
            next_cursor = str(end_idx) if end_idx < len(user_orders) else None

            return CursorResult.create(
                items=page_orders, next_cursor=next_cursor, page_size=page_size
            )

        # Test first page
        result = await get_user_orders_cursor(user_id=1, ctx=mock_context, cursor=None, page_size=3)

        assert isinstance(result, CursorResult)
        assert len(result.items) == 3
        assert result.has_next is True
        assert result.next_cursor == "3"

        # Verify orders belong to correct user
        for order in result.items:
            assert order.user_id == 1

        # Test second page
        result = await get_user_orders_cursor(user_id=1, ctx=mock_context, cursor="3", page_size=3)

        assert len(result.items) == 2  # Remaining orders
        assert result.has_next is False
        assert result.next_cursor is None


class TestPaginationParams:
    """Test pagination parameter handling in real scenarios."""

    @pytest.mark.asyncio
    async def test_pagination_params_helper(self, app, mock_context, sample_users):
        """Test using PaginationParams helper class."""
        user_cls = app._test_user

        @app.retrieve
        async def list_users_with_params(
            ctx: EnrichContext, pagination: PaginationParams | None = None
        ) -> PageResult[user_cls]:
            """List users using PaginationParams helper."""
            if pagination is None:
                pagination = PaginationParams()

            # Use pagination helper methods
            start_idx = pagination.get_offset()
            limit = pagination.get_limit()

            # Apply pagination
            page_users = sample_users[start_idx : start_idx + limit]
            has_next = start_idx + limit < len(sample_users)

            return PageResult.create(
                items=page_users,
                page=pagination.page,
                page_size=pagination.page_size,
                has_next=has_next,
                total_items=len(sample_users),
            )

        # Test with default pagination
        result = await list_users_with_params(ctx=mock_context, pagination=None)

        assert len(result.items) == 50  # Default page_size
        assert result.page == 1
        assert result.has_next is True

        # Test with custom pagination
        params = PaginationParams(page=3, page_size=20)
        result = await list_users_with_params(ctx=mock_context, pagination=params)

        assert len(result.items) == 20
        assert result.page == 3
        assert result.items[0].id == 41  # (3-1) * 20 + 1

    @pytest.mark.asyncio
    async def test_cursor_params_helper(self, app, mock_context, sample_users):
        """Test using CursorParams helper class."""
        user_cls = app._test_user

        @app.retrieve
        async def list_users_with_cursor_params(
            ctx: EnrichContext, cursor_params: CursorParams | None = None
        ) -> CursorResult[user_cls]:
            """List users using CursorParams helper."""
            if cursor_params is None:
                cursor_params = CursorParams()

            start_idx = 0 if cursor_params.cursor is None else int(cursor_params.cursor)
            end_idx = start_idx + cursor_params.page_size

            page_users = sample_users[start_idx:end_idx]
            next_cursor = str(end_idx) if end_idx < len(sample_users) else None

            return CursorResult.create(
                items=page_users, next_cursor=next_cursor, page_size=cursor_params.page_size
            )

        # Test with default cursor params
        result = await list_users_with_cursor_params(ctx=mock_context, cursor_params=None)

        assert len(result.items) == 50  # Default page_size
        assert result.has_next is True
        assert result.next_cursor == "50"

        # Test with custom cursor params
        params = CursorParams(cursor="30", page_size=10)
        result = await list_users_with_cursor_params(ctx=mock_context, cursor_params=params)

        assert len(result.items) == 10
        assert result.items[0].id == 31  # Starting from cursor position
        assert result.next_cursor == "40"


class TestRealWorldScenarios:
    """Test pagination in realistic scenarios."""

    @pytest.mark.asyncio
    async def test_large_dataset_performance(self, app, mock_context):
        """Test pagination with large dataset simulation."""
        user_cls = app._test_user

        # Create a large dataset
        large_dataset = [
            user_cls(id=i, name=f"User {i}", created_at=datetime(2023, 1, 1))
            for i in range(1, 10001)  # 10,000 users
        ]

        @app.retrieve
        async def list_large_dataset(
            ctx: EnrichContext, page: int = 1, page_size: int = 100
        ) -> PageResult[user_cls]:
            """List from large dataset."""
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size

            page_users = large_dataset[start_idx:end_idx]
            has_next = end_idx < len(large_dataset)

            return PageResult.create(
                items=page_users,
                page=page,
                page_size=page_size,
                has_next=has_next,
                total_items=len(large_dataset),
            )

        # Test pagination through large dataset
        result = await list_large_dataset(ctx=mock_context, page=50, page_size=100)

        assert len(result.items) == 100
        assert result.page == 50
        assert result.total_items == 10000
        assert result.total_pages == 100
        assert result.has_next is True
        assert result.has_previous is True

        # Verify correct items
        assert result.items[0].id == 4901  # (50-1) * 100 + 1
        assert result.items[99].id == 5000

    @pytest.mark.asyncio
    async def test_pagination_edge_cases(self, app, mock_context):
        """Test pagination edge cases."""
        user_cls = app._test_user

        # Dataset with exactly one page
        single_page_data = [
            user_cls(id=i, name=f"User {i}", created_at=datetime(2023, 1, 1))
            for i in range(1, 6)  # 5 users
        ]

        @app.retrieve
        async def list_single_page(
            ctx: EnrichContext, page: int = 1, page_size: int = 10
        ) -> PageResult[user_cls]:
            """List single page dataset."""
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size

            page_users = single_page_data[start_idx:end_idx]
            has_next = end_idx < len(single_page_data)

            return PageResult.create(
                items=page_users,
                page=page,
                page_size=page_size,
                has_next=has_next,
                total_items=len(single_page_data),
            )

        # Test single page
        result = await list_single_page(ctx=mock_context, page=1, page_size=10)

        assert len(result.items) == 5
        assert result.page == 1
        assert result.has_next is False
        assert result.has_previous is False
        assert result.total_pages == 1

        # Test requesting page beyond available data
        result = await list_single_page(ctx=mock_context, page=2, page_size=10)

        assert len(result.items) == 0
        assert result.page == 2
        assert result.has_next is False
        assert result.has_previous is True
