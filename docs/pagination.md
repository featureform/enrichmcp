# Pagination Guide

EnrichMCP provides comprehensive pagination support for both page-based and cursor-based pagination patterns. This guide shows you how to implement pagination in your MCP resources and relationship resolvers.

## Quick Start

```python
from enrichmcp import EnrichMCP, EnrichModel, PageResult, CursorResult
from pydantic import Field

app = EnrichMCP(title="My API", description="API with pagination")


@app.entity
class User(EnrichModel):
    """User entity."""

    id: int = Field(description="User ID")
    name: str = Field(description="User name")


# Page-based pagination
@app.retrieve
async def list_users(page: int = 1, page_size: int = 50) -> PageResult[User]:
    """List users with page-based pagination."""
    users, total = await db.get_users_page(page, page_size)
    return PageResult.create(
        items=users,
        page=page,
        page_size=page_size,
        has_next=page * page_size < total,
        total_items=total,
    )


# Cursor-based pagination
@app.retrieve
async def stream_users(cursor: str | None = None, limit: int = 50) -> CursorResult[User]:
    """Stream users with cursor-based pagination."""
    users, next_cursor = await db.get_users_cursor(cursor, limit)
    return CursorResult.create(items=users, next_cursor=next_cursor, page_size=limit)
```

## Pagination Types

### Page-Based Pagination

Page-based pagination uses page numbers and is ideal for:
- User interfaces with page numbers ("Page 1 of 10")
- Admin panels and reports
- Scenarios where users need to jump to specific pages
- Small to medium datasets (< 100K records)

```python
from enrichmcp import PageResult, PaginationParams


@app.retrieve
async def list_orders(
    page: int = 1, page_size: int = 25, status: str | None = None
) -> PageResult[Order]:
    """List orders with filtering and pagination."""

    # Apply filters and pagination
    orders, total = await db.get_orders(page=page, page_size=page_size, status=status)

    return PageResult.create(
        items=orders,
        page=page,
        page_size=page_size,
        has_next=page * page_size < total,
        total_items=total,  # Optional but recommended
    )
```

#### PageResult Properties

```python
result = PageResult.create(items, page=2, page_size=10, has_next=True, total_items=45)

# Navigation properties
result.page  # 2 - Current page number
result.has_next  # True - More pages available
result.has_previous  # True - Previous pages available (page > 1)
result.total_pages  # 5 - Total pages (if total_items provided)

# Get parameters for next page
next_params = result.get_next_params()  # {"page": 3, "page_size": 10}
```

### Cursor-Based Pagination

Cursor-based pagination uses cursors and is ideal for:
- Real-time feeds and timelines
- Large datasets (1M+ records)
- Mobile infinite scroll
- Scenarios where data changes frequently
- High-performance APIs

```python
from enrichmcp import CursorResult, CursorParams


@app.retrieve
async def stream_notifications(
    cursor: str | None = None, limit: int = 20
) -> CursorResult[Notification]:
    """Stream notifications with cursor pagination."""

    notifications, next_cursor = await db.get_notifications_after_cursor(cursor=cursor, limit=limit)

    return CursorResult.create(
        items=notifications,
        next_cursor=next_cursor,  # None if no more items
        page_size=limit,
    )
```

#### CursorResult Properties

```python
result = CursorResult.create(items, next_cursor="abc123", page_size=20)

# Navigation properties
result.has_next  # True - More items available
result.next_cursor  # "abc123" - Cursor for next page

# Get parameters for next page
next_params = result.get_next_params()  # {"cursor": "abc123", "page_size": 20}
```

## Pagination Helper Classes

### PaginationParams

Use `PaginationParams` for consistent page-based pagination parameters:

```python
from enrichmcp import PaginationParams


@app.retrieve
async def search_users(query: str, pagination: PaginationParams | None = None) -> PageResult[User]:
    """Search users with pagination helper."""
    if pagination is None:
        pagination = PaginationParams()

    # Use helper methods
    offset = pagination.get_offset()  # (page - 1) * page_size
    limit = pagination.get_limit()  # page_size

    users, total = await db.search_users(
        query=query,
        offset=offset,
        limit=limit,
        order_by=pagination.order_by,
        order_direction=pagination.order_direction,
    )

    return PageResult.create(
        items=users,
        page=pagination.page,
        page_size=pagination.page_size,
        has_next=offset + limit < total,
        total_items=total,
    )
```

### CursorParams

Use `CursorParams` for consistent cursor-based pagination:

```python
from enrichmcp import CursorParams


@app.retrieve
async def list_events(
    event_type: str | None = None, cursor_params: CursorParams | None = None
) -> CursorResult[Event]:
    """List events with cursor pagination."""
    if cursor_params is None:
        cursor_params = CursorParams()

    events, next_cursor = await db.get_events(
        event_type=event_type,
        cursor=cursor_params.cursor,
        limit=cursor_params.page_size,
        order_by=cursor_params.order_by,
        order_direction=cursor_params.order_direction,
    )

    return CursorResult.create(
        items=events, next_cursor=next_cursor, page_size=cursor_params.page_size
    )
```

## Paginated Relationships

You can also paginate relationship resolvers:

```python
@app.entity
class User(EnrichModel):
    id: int = Field(description="User ID")
    orders: list["Order"] = Relationship(description="User orders")

@User.orders.resolver
async def get_user_orders(
    user_id: int,
    page: int = 1,
    page_size: int = 10,
    ctx: EnrichContext
) -> PageResult[Order]:
    """Get user orders with pagination."""
    db = ctx.request_context.lifespan_context["db"]

    orders, total = await db.get_user_orders(
        user_id=user_id,
        page=page,
        page_size=page_size
    )

    return PageResult.create(
        items=orders,
        page=page,
        page_size=page_size,
        has_next=page * page_size < total,
        total_items=total
    )
```

## Database Integration Examples

### SQLite Example

```python
async def get_users_page(self, page: int, page_size: int) -> tuple[list[dict], int]:
    """Get paginated users from SQLite."""
    # Get total count
    count_cursor = self.conn.cursor()
    count_cursor.execute("SELECT COUNT(*) FROM users")
    total = count_cursor.fetchone()[0]

    # Get paginated results
    offset = (page - 1) * page_size
    cursor = self.conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY id LIMIT ? OFFSET ?", (page_size, offset))

    users = [dict(row) for row in cursor.fetchall()]
    return users, total


async def get_users_cursor(self, cursor: str | None, limit: int) -> tuple[list[dict], str | None]:
    """Get cursor-paginated users from SQLite."""
    # Parse cursor (could be last seen ID)
    last_id = 0 if cursor is None else int(cursor)

    # Fetch one extra to check if there are more
    db_cursor = self.conn.cursor()
    db_cursor.execute("SELECT * FROM users WHERE id > ? ORDER BY id LIMIT ?", (last_id, limit + 1))

    users = [dict(row) for row in db_cursor.fetchall()]

    # Check if there are more results
    has_more = len(users) > limit
    if has_more:
        users = users[:-1]  # Remove the extra item
        next_cursor = str(users[-1]["id"])  # Use last ID as cursor
    else:
        next_cursor = None

    return users, next_cursor
```

### PostgreSQL with asyncpg

```python
async def get_users_page(self, page: int, page_size: int) -> tuple[list[dict], int]:
    """Get paginated users from PostgreSQL."""
    # Get total count
    total = await self.conn.fetchval("SELECT COUNT(*) FROM users")

    # Get paginated results
    offset = (page - 1) * page_size
    rows = await self.conn.fetch(
        "SELECT * FROM users ORDER BY id LIMIT $1 OFFSET $2", page_size, offset
    )

    users = [dict(row) for row in rows]
    return users, total
```

## Performance Considerations

### Page-Based Pagination

- **OFFSET Performance**: `OFFSET` becomes slow with large offsets (> 10K)
- **Solution**: Add database indexes on ORDER BY columns
- **Alternative**: Use cursor-based pagination for large datasets

```sql
-- Add index for better OFFSET performance
CREATE INDEX idx_users_created_at ON users(created_at);
```

### Cursor-Based Pagination

- **Best Performance**: No OFFSET required, scales to millions of records
- **Requirement**: Needs a sortable, unique cursor field (ID, timestamp)
- **Trade-off**: Can't jump to arbitrary pages

```python
# Efficient cursor-based query
async def get_users_cursor(self, cursor: str | None, limit: int):
    """Efficient cursor pagination."""
    if cursor is None:
        # First page
        query = "SELECT * FROM users ORDER BY created_at, id LIMIT $1"
        params = [limit + 1]
    else:
        # Parse cursor (could be "timestamp:id")
        timestamp, last_id = cursor.split(":")
        query = """
            SELECT * FROM users
            WHERE (created_at, id) > ($1, $2)
            ORDER BY created_at, id
            LIMIT $3
        """
        params = [timestamp, int(last_id), limit + 1]

    rows = await self.conn.fetch(query, *params)
    # ... handle results
```

## Best Practices

### 1. Choose the Right Pagination Type

- **Page numbers**: Admin interfaces, reports, small datasets
- **Cursors**: Real-time feeds, mobile apps, large datasets

### 2. Set Reasonable Limits

```python
# Good defaults
PAGE_SIZE_DEFAULT = 50
PAGE_SIZE_MAX = 1000
CURSOR_LIMIT_DEFAULT = 20
CURSOR_LIMIT_MAX = 100

page_size: int = Field(default=50, ge=1, le=1000)
```

### 3. Include Total Counts Wisely

```python
# Include total for small datasets
if total_items < 10000:
    return PageResult.create(..., total_items=total)
else:
    # Skip expensive COUNT for large datasets
    return PageResult.create(..., total_items=None)
```

### 4. Add Filtering and Sorting

```python
@app.retrieve
async def search_orders(
    status: str | None = None,
    user_id: int | None = None,
    page: int = 1,
    page_size: int = 25,
    order_by: str = "created_at",
    order_direction: str = "desc",
) -> PageResult[Order]:
    """Searchable, sortable, paginated orders."""
    # Implementation with filters
```

### 5. Handle Edge Cases

```python
# Empty results
if not items:
    return PageResult.create(
        items=[], page=page, page_size=page_size, has_next=False, total_items=0
    )

# Page beyond available data
if page > total_pages and total_pages > 0:
    # Return empty page or redirect to last page
    return PageResult.create(
        items=[], page=page, page_size=page_size, has_next=False, total_items=total
    )
```

## Generic Pagination Handling

The `PaginatedResult` protocol allows you to write generic code that works with both pagination types:

```python
from enrichmcp import PaginatedResult


async def export_paginated_data(
    fetcher: Callable[..., Awaitable[PaginatedResult[T]]], **initial_params
) -> list[T]:
    """Export all pages of data."""
    all_items = []
    params = initial_params.copy()

    while True:
        result = await fetcher(**params)
        all_items.extend(result.items)

        if not result.has_next:
            break

        # Get parameters for next page (works for both page and cursor)
        params.update(result.get_next_params())

    return all_items


# Works with both pagination types
users = await export_paginated_data(list_users, page=1, page_size=100)
events = await export_paginated_data(stream_events, cursor=None, limit=50)
```

## Testing Pagination

```python
import pytest
from enrichmcp import PageResult, CursorResult


@pytest.mark.asyncio
async def test_page_pagination():
    """Test page-based pagination."""
    result = await list_users(page=1, page_size=10)

    assert isinstance(result, PageResult)
    assert len(result.items) <= 10
    assert result.page == 1
    assert result.page_size == 10

    if result.has_next:
        next_result = await list_users(page=2, page_size=10)
        assert next_result.page == 2


@pytest.mark.asyncio
async def test_cursor_pagination():
    """Test cursor-based pagination."""
    result = await stream_users(cursor=None, limit=10)

    assert isinstance(result, CursorResult)
    assert len(result.items) <= 10

    if result.has_next:
        next_result = await stream_users(cursor=result.next_cursor, limit=10)
        assert next_result.next_cursor != result.next_cursor
```

## Migration Guide

### From Non-Paginated to Paginated

```python
# Before: Returns all items
@app.retrieve
async def list_users() -> list[User]:
    return await db.get_all_users()


# After: Add pagination parameters
@app.retrieve
async def list_users(page: int = 1, page_size: int = 50) -> PageResult[User]:
    users, total = await db.get_users_page(page, page_size)
    return PageResult.create(
        items=users,
        page=page,
        page_size=page_size,
        has_next=page * page_size < total,
        total_items=total,
    )
```

The old endpoint remains backward compatible - clients can call it without pagination parameters and get the first page.
