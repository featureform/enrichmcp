# enrichmcp

**Transform Your Data Model into an MCP API**

EnrichMCP (by [Featureform](https://featureform.com)) brings the power of type-safe, relationship-aware data models to AI agents. Built on top of FastMCP, it provides the missing data layer that enables **Agentic Enrichment** - giving AI agents the ability to discover, understand, and navigate your data through intelligent schema introspection and automatic tool generation.

[![CI](https://github.com/featureform/enrichmcp/actions/workflows/ci.yml/badge.svg)](https://github.com/featureform/enrichmcp/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/featureform/enrichmcp/branch/main/graph/badge.svg)](https://codecov.io/gh/featureform/enrichmcp)
[![Documentation](https://img.shields.io/badge/docs-github%20pages-blue.svg)](https://featureform.github.io/enrichmcp)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/featureform/enrichmcp/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/enrichmcp.svg)](https://pypi.org/project/enrichmcp/)

## What is Agentic Enrichment?

Traditional APIs require extensive documentation and hand-holding for AI agents to use effectively. Agentic Enrichment flips this model - instead of teaching AI about your API, your API teaches itself to AI. Through intelligent schema introspection, relationship mapping, and automatic tool generation, AI agents can naturally discover and navigate your data model as if they inherently understand your domain.

## Why EnrichMCP?

While FastMCP provides the protocol layer for AI-tool communication, real-world applications need more:

- **🔍 Schema Introspection**: AI agents can explore your entire data model through a single `explore_data_model()` call
- **🔗 Relationship Intelligence**: GraphQL-inspired traversal with automatic resolver generation
- **🛡️ Type Safety**: Full Pydantic validation with rich field descriptions
- **🚀 Zero Boilerplate**: Decorators handle all the MCP protocol details
- **📖 Self-Documenting**: Every entity, field, and relationship includes descriptions that AI agents can understand

### EnrichMCP vs FastMCP

| Feature | FastMCP | EnrichMCP |
|---------|---------|-----------|
| Protocol Implementation | ✅ | ✅ (via FastMCP) |
| Type Safety | Basic | Full Pydantic Models |
| Relationships | Manual | Automatic with Resolvers |
| Schema Discovery | Manual | Automatic Introspection |
| Tool Generation | Manual | Automatic from Models |
| Data Focus | Generic | Data Model Optimized |

## Installation

```bash
pip install enrichmcp
```

## Quick Start

```python
from enrichmcp import EnrichMCP, EnrichModel, Relationship
from pydantic import Field

# Create your MCP application
app = EnrichMCP(title="Customer API", description="Customer data model for AI agents")


# Define your data model with rich descriptions
@app.entity
class Customer(EnrichModel):
    """Represents a customer in our system.

    Contains core customer information and relationships to their orders.
    Used for customer service, analytics, and order processing.
    """

    id: int = Field(description="Unique customer identifier")
    name: str = Field(description="Customer's full name")
    email: str = Field(description="Primary contact email")
    status: str = Field(description="Account status: active, suspended, or churned")
    created_at: datetime = Field(description="When the customer joined")

    # Define relationships that AI can traverse
    orders: list["Order"] = Relationship(description="All orders placed by this customer")


@app.entity
class Order(EnrichModel):
    """Represents a customer order.

    Tracks order details, status, and relationships to customers and products.
    """

    id: int = Field(description="Unique order identifier")
    customer_id: int = Field(description="Customer who placed this order")
    total: float = Field(description="Total order amount in USD")
    status: str = Field(description="Order status: pending, shipped, delivered")
    created_at: datetime = Field(description="When the order was placed")

    # Relationships
    customer: Customer = Relationship(description="Customer who placed this order")
    items: list["OrderItem"] = Relationship(description="Individual items in this order")


# Define how relationships are resolved
@Customer.orders.resolver
async def get_customer_orders(customer_id: int) -> list[Order]:
    """Fetch all orders for a customer from the database."""
    # Your database logic here
    return await db.get_orders_by_customer(customer_id)


@Order.customer.resolver
async def get_order_customer(order_id: int) -> Customer:
    """Fetch the customer who placed an order."""
    # Your database logic here
    return await db.get_customer_by_order(order_id)


# Define root access points for AI agents
@app.resource
async def get_customer(customer_id: int) -> Customer:
    """Retrieve a specific customer by ID.

    This is a primary entry point for AI agents to access customer data.
    From here, they can traverse to related orders and other data.
    """
    return await db.get_customer(customer_id)


@app.resource
async def list_customers(status: str | None = None) -> list[Customer]:
    """List all customers, optionally filtered by status.

    Useful for AI agents to discover customers and analyze patterns.
    """
    return await db.list_customers(status=status)


# Run the server
if __name__ == "__main__":
    app.run()
```

## How AI Agents Use Your API

When an AI agent connects to your EnrichMCP API, it can:

1. **Discover the Model**: Call `explore_data_model()` to understand all entities and relationships
2. **Navigate Relationships**: Follow relationships between entities naturally
3. **Access Data**: Use generated tools with full type safety and validation

Example AI agent interaction:
```
AI: "Show me all active customers and their recent orders"

1. AI calls explore_data_model() - discovers Customer and Order entities
2. AI calls list_customers(status="active") - gets active customers
3. AI calls Customer.orders resolver for each customer - gets their orders
4. AI presents the organized data to the user
```

## Key Features

### 🔍 Automatic Schema Discovery

AI agents can explore your entire data model:

```python
# AI agents automatically get a tool called `explore_data_model()`
model_info = await explore_data_model()
# Returns complete schema with entities, fields, relationships, and descriptions
```

### 🔗 Relationship Traversal

Define relationships once, AI agents navigate naturally:

```python
@Customer.orders.resolver
async def get_orders(customer_id: int) -> list[Order]:
    """AI agents can call this to get customer orders"""
    return await fetch_orders(customer_id)
```

### 🛡️ Type Safety & Validation

Full Pydantic validation on all inputs and outputs:

```python
# AI provides invalid data? Automatic validation errors
# AI receives data? Guaranteed to match your schema
```

### 📖 Rich Descriptions

Every element includes descriptions for AI understanding:

```python
email: str = Field(description="Customer's primary email for communications")
# AI knows exactly what this field represents
```

## Advanced Features

### Context Management

Pass database connections and auth through context:

```python
from enrichmcp import EnrichContext


@app.resource
async def get_customer(customer_id: int, context: EnrichContext) -> Customer:
    """Access database through context."""
    return await context.db.get_customer(customer_id)
```

### Error Handling

Built-in error types that AI agents understand:

```python
from enrichmcp.errors import NotFoundError, ValidationError


@app.resource
async def get_customer(customer_id: int) -> Customer:
    customer = await db.get_customer(customer_id)
    if not customer:
        raise NotFoundError(f"Customer {customer_id} not found")
    return customer
```

### Pagination

Handle large datasets efficiently with built-in pagination support:

```python
from enrichmcp import PageResult, CursorResult


# Page-based pagination (ideal for UIs)
@app.resource
async def list_customers(page: int = 1, page_size: int = 50) -> PageResult[Customer]:
    """List customers with page-based pagination."""
    customers, total = await db.get_customers_page(page, page_size)
    return PageResult.create(
        items=customers,
        page=page,
        page_size=page_size,
        has_next=page * page_size < total,
        total_items=total,
    )


# Cursor-based pagination (ideal for real-time feeds)
@app.resource
async def stream_orders(cursor: str | None = None, limit: int = 20) -> CursorResult[Order]:
    """Stream orders with cursor-based pagination."""
    orders, next_cursor = await db.get_orders_cursor(cursor, limit)
    return CursorResult.create(items=orders, next_cursor=next_cursor, page_size=limit)


# Paginated relationships
@Customer.orders.resolver
async def get_customer_orders(
    customer_id: int, page: int = 1, page_size: int = 10
) -> PageResult[Order]:
    """Get customer orders with pagination."""
    orders, total = await db.get_customer_orders_page(customer_id, page, page_size)
    return PageResult.create(
        items=orders,
        page=page,
        page_size=page_size,
        has_next=page * page_size < total,
        total_items=total,
    )
```

See the [Pagination Guide](docs/pagination.md) for comprehensive examples and best practices.

## Development

```bash
# Clone the repository
git clone https://github.com/featureform/enrichmcp
cd enrichmcp

# Set up development environment
make setup

# Run tests
make test

# Format code
make format

# Run linters
make lint
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## Support

- 📖 [Documentation](https://featureform.github.io/enrichmcp)
- 🐛 [Issue Tracker](https://github.com/featureform/enrichmcp/issues)
- 💬 [Discussions](https://github.com/featureform/enrichmcp/discussions)

## License

EnrichMCP is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

---

Built with ❤️ by [Featureform](https://featureform.com)

⭐ If you find EnrichMCP useful, please star this repository!
