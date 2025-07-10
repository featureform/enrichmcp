# EnrichMCP

**The ORM for AI Agents - Turn your data model into a semantic MCP layer**

[![CI](https://github.com/featureform/enrichmcp/actions/workflows/ci.yml/badge.svg)](https://github.com/featureform/enrichmcp/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/featureform/enrichmcp/branch/main/graph/badge.svg)](https://codecov.io/gh/featureform/enrichmcp)
[![PyPI](https://img.shields.io/pypi/v/enrichmcp.svg)](https://pypi.org/project/enrichmcp/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/featureform/enrichmcp/blob/main/LICENSE)
[![Docs](https://img.shields.io/badge/docs-website-blue.svg)](https://featureform.github.io/enrichmcp)

EnrichMCP is a Python framework that helps AI agents understand and navigate your data. Built on MCP (Model Context Protocol), it adds a semantic layer that turns your data model into typed, discoverable tools - like an ORM for AI.

## What is EnrichMCP?

Think of it as SQLAlchemy for AI agents. EnrichMCP automatically:

- **Generates typed tools** from your data models
- **Handles relationships** between entities (users → orders → products)
- **Provides schema discovery** so AI agents understand your data structure
- **Validates all inputs/outputs** with Pydantic models
- **Works with any backend** - databases, APIs, or custom logic

## Installation

```bash
pip install enrichmcp

# With SQLAlchemy support
pip install enrichmcp[sqlalchemy]
```

## Show Me Code

### Option 1: I Have SQLAlchemy Models (30 seconds)

Transform your existing SQLAlchemy models into an AI-navigable API:


```python
from enrichmcp import EnrichMCP
from enrichmcp.sqlalchemy import include_sqlalchemy_models, sqlalchemy_lifespan, EnrichSQLAlchemyMixin
from sqlalchemy import ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")

# Add the mixin to your declarative base
class Base(DeclarativeBase, EnrichSQLAlchemyMixin):
    pass

class User(Base):
    """User account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, info={"description": "Unique user ID"})
    email: Mapped[str] = mapped_column(unique=True, info={"description": "Email address"})
    status: Mapped[str] = mapped_column(default="active", info={"description": "Account status"})
    orders: Mapped[list["Order"]] = relationship(back_populates="user", info={"description": "All orders for this user"})

class Order(Base):
    """Customer order."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, info={"description": "Order ID"})
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), info={"description": "Owner user ID"})
    total: Mapped[float] = mapped_column(info={"description": "Order total"})
    user: Mapped[User] = relationship(back_populates="orders", info={"description": "User who placed the order"})

# That's it! Create your MCP app
app = EnrichMCP(
    "E-commerce Data",
    "API generated from SQLAlchemy models",
    lifespan=sqlalchemy_lifespan(Base, engine, cleanup_db_file=True),
)
include_sqlalchemy_models(app, Base)

if __name__ == "__main__":
    app.run()
```
AI agents can now:
- `explore_data_model()` - understand your entire schema
- `list_users(status='active')` - query with filters
- `get_user(id=123)` - fetch specific records
- Navigate relationships: `user.orders` → `order.user`

### Option 2: I Have REST APIs (2 minutes)

Wrap your existing APIs with semantic understanding:

```python
from typing import Literal
from enrichmcp import EnrichMCP, EnrichModel, Relationship
from pydantic import Field
import httpx

app = EnrichMCP("API Gateway", "Wrapper around existing REST APIs")
http = httpx.AsyncClient(base_url="https://api.example.com")

@app.entity
class Customer(EnrichModel):
    """Customer in our CRM system."""

    id: int = Field(description="Unique customer ID")
    email: str = Field(description="Primary contact email")
    tier: Literal["free", "pro", "enterprise"] = Field(
        description="Subscription tier"
    )

    # Define navigable relationships
    orders: list["Order"] = Relationship(description="Customer's purchase history")

@app.entity
class Order(EnrichModel):
    """Customer order from our e-commerce platform."""

    id: int = Field(description="Order ID")
    customer_id: int = Field(description="Associated customer")
    total: float = Field(description="Order total in USD")
    status: Literal["pending", "shipped", "delivered"] = Field(
        description="Order status"
    )

    customer: Customer = Relationship(description="Customer who placed this order")

# Define how to fetch data
@app.retrieve
async def get_customer(customer_id: int) -> Customer:
    """Fetch customer from CRM API."""
    response = await http.get(f"/api/customers/{customer_id}")
    return Customer(**response.json())

# Define relationship resolvers
@Customer.orders.resolver
async def get_customer_orders(customer_id: int) -> list[Order]:
    """Fetch orders for a customer."""
    response = await http.get(f"/api/customers/{customer_id}/orders")
    return [Order(**order) for order in response.json()]

@Order.customer.resolver
async def get_order_customer(order_id: int) -> Customer:
    """Fetch the customer for an order."""
    response = await http.get(f"/api/orders/{order_id}/customer")
    return Customer(**response.json())

app.run()
```

### Option 3: I Want Full Control (5 minutes)

Build a complete data layer with custom logic:

```python
from enrichmcp import EnrichMCP, EnrichModel, Relationship, EnrichContext
from datetime import datetime
from decimal import Decimal
from pydantic import Field

app = EnrichMCP("Analytics Platform", "Custom analytics API")

db = ...  # your database connection

@app.entity
class User(EnrichModel):
    """User with computed analytics fields."""

    id: int = Field(description="User ID")
    email: str = Field(description="Contact email")
    created_at: datetime = Field(description="Registration date")

    # Computed fields
    lifetime_value: Decimal = Field(description="Total revenue from user")
    churn_risk: float = Field(description="ML-predicted churn probability 0-1")

    # Relationships
    orders: list["Order"] = Relationship(description="Purchase history")
    segments: list["Segment"] = Relationship(description="Marketing segments")

@app.entity
class Segment(EnrichModel):
    """Dynamic user segment for marketing."""

    name: str = Field(description="Segment name")
    criteria: dict = Field(description="Segment criteria")
    users: list[User] = Relationship(description="Users in this segment")


@app.entity
class Order(EnrichModel):
    """Simplified order record."""

    id: int = Field(description="Order ID")
    user_id: int = Field(description="Owner user ID")
    total: Decimal = Field(description="Order total")

@User.orders.resolver
async def list_user_orders(user_id: int) -> list[Order]:
    """Fetch orders for a user."""
    rows = await db.query(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC",
        user_id,
    )
    return [Order(**row) for row in rows]

@User.segments.resolver
async def list_user_segments(user_id: int) -> list[Segment]:
    """Fetch segments that include the user."""
    rows = await db.query(
        "SELECT s.* FROM segments s JOIN user_segments us ON s.name = us.segment_name WHERE us.user_id = ?",
        user_id,
    )
    return [Segment(**row) for row in rows]

@Segment.users.resolver
async def list_segment_users(name: str) -> list[User]:
    """List users in a segment."""
    rows = await db.query(
        "SELECT u.* FROM users u JOIN user_segments us ON u.id = us.user_id WHERE us.segment_name = ?",
        name,
    )
    return [User(**row) for row in rows]

# Complex resource with business logic
@app.retrieve
async def find_high_value_at_risk_users(
    lifetime_value_min: Decimal = 1000,
    churn_risk_min: float = 0.7,
    limit: int = 100
) -> list[User]:
    """Find valuable customers likely to churn."""
    users = await db.query(
        """
        SELECT * FROM users
        WHERE lifetime_value >= ? AND churn_risk >= ?
        ORDER BY lifetime_value DESC
        LIMIT ?
        """,
        lifetime_value_min, churn_risk_min, limit
    )
    return [User(**u) for u in users]

# Async computed field resolver
@User.lifetime_value.resolver
async def calculate_lifetime_value(user_id: int) -> Decimal:
    """Calculate total revenue from user's orders."""
    total = await db.query_single(
        "SELECT SUM(total) FROM orders WHERE user_id = ?",
        user_id
    )
    return Decimal(str(total or 0))

# ML-powered field
@User.churn_risk.resolver
async def predict_churn_risk(user_id: int, context: EnrichContext) -> float:
    """Run churn prediction model."""
    features = await gather_user_features(user_id)
    model = context.get("ml_models")["churn"]
    return float(model.predict_proba(features)[0][1])

app.run()
```

## Key Features

### 🔍 Automatic Schema Discovery

AI agents explore your entire data model with one call:

```python
schema = await explore_data_model()
# Returns complete schema with entities, fields, types, and relationships
```

### 🔗 Relationship Navigation

Define relationships once, AI agents traverse naturally:

```python
# AI can navigate: user → orders → products → categories
user = await get_user(123)
orders = await user.orders()  # Automatic resolver
products = await orders[0].products()
```

### 🛡️ Type Safety & Validation

Full Pydantic validation on every interaction:

```python
@app.entity
class Order(EnrichModel):
    total: float = Field(ge=0, description="Must be positive")
    email: EmailStr = Field(description="Customer email")
    status: Literal["pending", "shipped", "delivered"]
```
`describe_model()` will list these allowed values so agents know the valid options.

### ✏️ Mutability & CRUD

Fields are immutable by default. Mark them as mutable and use
auto-generated patch models for updates:

```python
@app.entity
class Customer(EnrichModel):
    id: int = Field(description="ID")
    email: str = Field(json_schema_extra={"mutable": True}, description="Email")

@app.create
async def create_customer(email: str) -> Customer:
    ...

@app.update
async def update_customer(cid: int, patch: Customer.PatchModel) -> Customer:
    ...

@app.delete
async def delete_customer(cid: int) -> bool:
    ...
```

### 📄 Pagination Built-in

Handle large datasets elegantly:

```python
from enrichmcp import PageResult

@app.retrieve
async def list_orders(
    page: int = 1,
    page_size: int = 50
) -> PageResult[Order]:
    orders, total = await db.get_orders_page(page, page_size)
    return PageResult.create(
        items=orders,
        page=page,
        page_size=page_size,
        total_items=total
    )
```

See the [Pagination Guide](https://featureform.github.io/enrichmcp/pagination) for more examples.

### 🔐 Context & Authentication

Pass auth, database connections, or any context:

```python
from pydantic import Field
from enrichmcp import EnrichModel

class UserProfile(EnrichModel):
    """User profile information."""

    user_id: int = Field(description="User ID")
    bio: str | None = Field(default=None, description="Short bio")

@app.retrieve
async def get_user_profile(user_id: int, context: EnrichContext) -> UserProfile:
    # Access context provided by MCP client
    auth_user = context.get("authenticated_user_id")
    if auth_user != user_id:
        raise PermissionError("Can only access your own profile")
    return await db.get_profile(user_id)
```

### ⚡ Request Caching

Reduce API overhead by storing results in a per-request, per-user, or global cache:

```python

@app.retrieve
async def get_customer(cid: int, ctx: EnrichContext) -> Customer:
    async def fetch() -> Customer:
        return await db.get_customer(cid)

    return await ctx.cache.get_or_set(f"customer:{cid}", fetch)
```

### 🧭 Parameter Hints

Provide examples and metadata for tool parameters using `EnrichParameter`:

```python
from enrichmcp import EnrichParameter

@app.retrieve
async def greet_user(name: str = EnrichParameter(description="user name", examples=["bob"])) -> str:
    return f"Hello {name}"
```

Tool descriptions will include the parameter type, description, and examples.

### 🌐 HTTP & SSE Support

Serve your API over standard output (default), SSE, or HTTP:

```python
app.run()  # stdio default
app.run(transport="streamable-http")
```

## Why EnrichMCP?

EnrichMCP adds three critical layers on top of MCP:

1. **Semantic Layer** - AI agents understand what your data means, not just its structure
2. **Data Layer** - Type-safe models with validation and relationships
3. **Control Layer** - Authentication, pagination, and business logic

The result: AI agents can work with your data as naturally as a developer using an ORM.

## Examples

Check out the [examples directory](examples/README.md):

- [hello_world](examples/hello_world) - The smallest possible EnrichMCP app
- [hello_world_http](examples/hello_world_http) - HTTP example using streamable HTTP
- [shop_api](examples/shop_api) - In-memory shop API with pagination and filters
- [shop_api_sqlite](examples/shop_api_sqlite) - SQLite-backed version
- [shop_api_gateway](examples/shop_api_gateway) - EnrichMCP as a gateway in front of FastAPI
- [sqlalchemy_shop](examples/sqlalchemy_shop) - Auto-generated API from SQLAlchemy models
- [mutable_crud](examples/mutable_crud) - Demonstrates mutable fields and CRUD decorators
- [caching](examples/caching) - Demonstrates ContextCache usage
- [basic_memory](examples/basic_memory) - Simple note-taking API using FileMemoryStore
- [openai_chat_agent](examples/openai_chat_agent) - Interactive chat client for MCP examples

## Documentation

- 📖 [Full Documentation](https://featureform.github.io/enrichmcp)
- 🚀 [Getting Started Guide](https://featureform.github.io/enrichmcp/getting-started)
- 🔧 [API Reference](https://featureform.github.io/enrichmcp/api)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Development Setup

The repository requires **Python&nbsp;3.11** or newer. The Makefile includes
commands to create a virtual environment and run the tests:

```bash
make setup            # create .venv and install dependencies
source .venv/bin/activate
make test             # run the test suite
```

This installs all development extras and pre-commit hooks so commands like
`make lint` or `make docs` work right away.

## License

Apache 2.0 - See [LICENSE](LICENSE)

---

Built by [Featureform](https://featureform.com) • [MCP Protocol](https://modelcontextprotocol.io)
