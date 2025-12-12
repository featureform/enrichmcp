# impl_test.md

## Simplified User, Item, Orders Example Based on implementation.md

### 1. Pseudo Classes

Simplified version focusing on essential search fields:

```python
from enrichmcp.redis import RedisEnrichMCP, RedisModel, RedisField

app = RedisEnrichMCP(
    title="E-commerce API",
    instructions="Manage users, items, and orders with Redis search",
    redis_url="redis://localhost:6379"
)

@app.redis_entity
class User(RedisModel):
    """A user in the e-commerce system."""

    # Class-level key template
    __redis_key__ = "user:{id}"

    # Primary key (excluded from storage)
    id: str = RedisField(description="Unique user identifier", key_component=True)

    # Text search - name is most important
    name: str = RedisField(
        description="User's full name",
        search_type="text",
        searchable=True,
        weight=2.0
    )

    # Tag filtering - role for permissions
    role: str = RedisField(
        description="User role: customer, admin, vendor",
        search_type="tag",
        filterable=True
    )

    # Numeric sorting - reputation for ranking
    reputation_score: int = RedisField(
        description="User reputation score (0-1000)",
        search_type="numeric",
        sortable=True
    )

    # Non-indexed fields
    email: str = RedisField(description="User email address")
    created_at: str = RedisField(description="Account creation timestamp")


@app.redis_entity
class Item(RedisModel):
    """A product item in the catalog."""

    # Class-level key template
    __redis_key__ = "item:{id}"

    # Primary key (excluded from storage)
    id: str = RedisField(description="Unique item identifier", key_component=True)

    # Text search - title and description
    title: str = RedisField(
        description="Item title/name",
        search_type="text",
        searchable=True,
        weight=3.0
    )

    description: str = RedisField(
        description="Item description",
        search_type="text",
        searchable=True,
        weight=1.0
    )

    # Tag filtering - category for browsing
    category: str = RedisField(
        description="Item category: electronics, clothing, books",
        search_type="tag",
        filterable=True
    )

    # Numeric sorting - price and rating
    price: float = RedisField(
        description="Item price in USD",
        search_type="numeric",
        sortable=True
    )

    rating: float = RedisField(
        description="Average rating (0.0-5.0)",
        search_type="numeric",
        sortable=True
    )

    # Vector similarity for recommendations
    product_embedding: list[float] = RedisField(
        description="Product embedding for similarity search",
        search_type="vector",
        dims=512,
        algorithm="hnsw",
        distance_metric="cosine"
    )

    # Non-indexed fields
    brand: str = RedisField(description="Item brand")
    stock_quantity: int = RedisField(description="Available stock quantity")


@app.redis_entity
class Order(RedisModel):
    """An order in the system."""

    # Class-level key template
    __redis_key__ = "order:{id}"

    # Primary key (excluded from storage)
    id: str = RedisField(description="Unique order identifier", key_component=True)

    # Tag filtering - status for order management
    status: str = RedisField(
        description="Order status: pending, shipped, delivered, cancelled",
        search_type="tag",
        filterable=True
    )

    # Numeric sorting - amount and timestamp
    total_amount: float = RedisField(
        description="Total order amount in USD",
        search_type="numeric",
        sortable=True
    )

    created_timestamp: int = RedisField(
        description="Order creation timestamp (Unix timestamp)",
        search_type="numeric",
        sortable=True
    )

    # Relationship fields (stored as IDs)
    user_id: str = RedisField(description="ID of the user who placed the order")
    item_ids: list[str] = RedisField(description="List of item IDs in the order")
```

### 2. Expected FT.CREATE Commands

Simplified Redis index creation:

```bash
# User index - name search, role filtering, reputation sorting
# Note: id field excluded since it's key_component=True
FT.CREATE user_idx ON JSON PREFIX 1 "user:" SCHEMA
    $.name AS name TEXT WEIGHT 2.0
    $.role AS role TAG
    $.reputation_score AS reputation_score NUMERIC SORTABLE

# Item index - title/description search, category filtering, price/rating sorting, vector similarity
# Note: id field excluded since it's key_component=True
FT.CREATE item_idx ON JSON PREFIX 1 "item:" SCHEMA
    $.title AS title TEXT WEIGHT 3.0
    $.description AS description TEXT WEIGHT 1.0
    $.category AS category TAG
    $.price AS price NUMERIC SORTABLE
    $.rating AS rating NUMERIC SORTABLE
    $.product_embedding AS product_embedding VECTOR HNSW 6 DIM 512 DISTANCE_METRIC COSINE

# Order index - status filtering, amount/timestamp sorting
# Note: id field excluded since it's key_component=True
FT.CREATE order_idx ON JSON PREFIX 1 "order:" SCHEMA
    $.status AS status TAG
    $.total_amount AS total_amount NUMERIC SORTABLE
    $.created_timestamp AS created_timestamp NUMERIC SORTABLE
```

### 3. Generated MCP Resources and RQE Queries

#### 3.1 User Resources

**Text Search Resource:**
```python
# MCP Resource: search_user_by_text
async def search_user_by_text(query: str, limit: int = 10, offset: int = 0) -> list[User]:
    """Search User by text content."""
```

**RQE Query:**
```bash
# Search for users by name
FT.SEARCH user_idx "john smith" LIMIT 0 10
```

**Tag Filter Resource:**
```python
# MCP Resource: filter_user_by_role
async def filter_user_by_role(role: str) -> list[User]:
    """Filter User by role."""
```

**RQE Query:**
```bash
# Filter users by role
FT.SEARCH user_idx "@role:admin" LIMIT 0 10
```

#### 3.2 Item Resources

**Text Search Resource:**
```python
# MCP Resource: search_item_by_text
async def search_item_by_text(query: str, limit: int = 10, offset: int = 0) -> list[Item]:
    """Search Item by text content."""
```

**RQE Query:**
```bash
# Search items by title and description
FT.SEARCH item_idx "bluetooth headphones" LIMIT 0 10
```

**Tag Filter Resource:**
```python
# MCP Resource: filter_item_by_category
async def filter_item_by_category(category: str) -> list[Item]:
    """Filter Item by category."""
```

**RQE Query:**
```bash
# Filter items by category
FT.SEARCH item_idx "@category:electronics" LIMIT 0 10
```

**Vector Search Resource:**
```python
# MCP Resource: search_similar_item
async def search_similar_item(vector: list[float], limit: int = 10, threshold: float = 0.8) -> list[Item]:
    """Find Item similar to the given vector."""
```

**RQE Query:**
```bash
# Find similar products
FT.SEARCH item_idx "*=>[KNN 10 @product_embedding $product_embedding_vec]"
    PARAMS 2 product_embedding_vec "0.1,0.2,0.3,..."
    DIALECT 2
```

#### 3.3 Order Resources

**Tag Filter Resource:**
```python
# MCP Resource: filter_order_by_status
async def filter_order_by_status(status: str) -> list[Order]:
    """Filter Order by status."""
```

**RQE Query:**
```bash
# Filter orders by status
FT.SEARCH order_idx "@status:shipped" LIMIT 0 10
```

### 4. Complex Query Examples

**Price Range Filtering:**
```bash
# Find electronics under $100
FT.SEARCH item_idx "@category:electronics @price:[0 100]"
    SORTBY price ASC LIMIT 0 10
```

**High-Value Recent Orders:**
```bash
# Find orders over $500 in last 30 days, sorted by amount
FT.SEARCH order_idx "@total_amount:[500 +inf] @created_timestamp:[1640995200 +inf]"
    SORTBY total_amount DESC LIMIT 0 20
```

**Combined Text and Filter:**
```bash
# Search for "laptop" in electronics, sorted by rating
FT.SEARCH item_idx "(laptop) @category:electronics"
    SORTBY rating DESC LIMIT 0 10
```

**Admin Users with High Reputation:**
```bash
# Find admin users with reputation > 800
FT.SEARCH user_idx "@role:admin @reputation_score:[800 +inf]"
    SORTBY reputation_score DESC LIMIT 0 5
```

### 5. Sample Data Storage

**User Document:**
- **Redis Key:** `user:user123`
- **JSON Value:** (id excluded since it's key_component=True)
```json
{
  "name": "John Smith",
  "role": "customer",
  "reputation_score": 750,
  "email": "john@example.com",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Item Document:**
- **Redis Key:** `item:item456`
- **JSON Value:** (id excluded since it's key_component=True)
```json
{
  "title": "Wireless Bluetooth Headphones",
  "description": "High-quality noise-cancelling headphones with 30-hour battery",
  "category": "electronics",
  "price": 199.99,
  "rating": 4.5,
  "product_embedding": [0.1, 0.2, 0.3, ...],
  "brand": "AudioTech",
  "stock_quantity": 25
}
```

**Order Document:**
- **Redis Key:** `order:order789`
- **JSON Value:** (id excluded since it's key_component=True)
```json
{
  "status": "shipped",
  "total_amount": 249.98,
  "created_timestamp": 1641024000,
  "user_id": "user123",
  "item_ids": ["item456", "item789"]
}
```

This simplified version focuses on the most essential search capabilities while demonstrating the full range of Redis search features: text search, tag filtering, numeric sorting, and vector similarity. Each entity has a clear purpose and the indices support realistic e-commerce use cases.
