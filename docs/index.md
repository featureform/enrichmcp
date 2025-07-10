# Welcome to enrichmcp

**Transform Your Data Model into an MCP API**

enrichmcp brings the power of type-safe, relationship-aware data models to AI agents. Built on top of [FastMCP](https://github.com/jlowin/fastmcp), it provides the missing data layer that enables **Agentic Enrichment** - giving AI agents the ability to discover, understand, and navigate your data through intelligent schema introspection.

## Quick Example

```python
from enrichmcp import EnrichMCP, EnrichModel, Relationship
from pydantic import Field

# Create your API
app = EnrichMCP("Customer API", "Customer data for AI agents")


# Define your data model
@app.entity
class Customer(EnrichModel):
    """A customer in our system."""

    id: int = Field(description="Unique customer ID")
    name: str = Field(description="Customer name")
    email: str = Field(description="Contact email")

    orders: list["Order"] = Relationship(description="Orders placed by this customer")


@app.entity
class Order(EnrichModel):
    """A customer order."""

    id: int = Field(description="Order ID")
    total: float = Field(description="Order total in USD")
    status: str = Field(description="Order status")

    customer: Customer = Relationship(description="Customer who placed this order")


# Define how relationships are resolved
@Customer.orders.resolver
async def get_customer_orders(customer_id: int) -> list[Order]:
    # Your database logic here
    return await db.get_orders_for_customer(customer_id)


# Create entry points for AI
@app.retrieve
async def get_customer(customer_id: int) -> Customer:
    """Get a customer by ID."""
    return await db.get_customer(customer_id)


# Run it!
app.run()

# Serve over HTTP instead of stdio
app.run(transport="streamable-http")
```

Already using SQLAlchemy? See how to
[turn existing models into an API](sqlalchemy.md) with just a few lines.

## Why enrichmcp?

### 🤖 Built for AI Agents

Unlike traditional APIs designed for humans, enrichmcp APIs are designed for AI:

- **Self-Describing**: Every element includes rich descriptions
- **Discoverable**: AI can explore your entire data model with one call
- **Navigable**: Relationships allow natural data traversal

### 🛡️ Type Safety First

Built on Pydantic, enrichmcp provides:

- **Automatic Validation**: Invalid data never reaches your code
- **IDE Support**: Full autocomplete and type hints
- **Runtime Safety**: Catch errors before they happen

### 🚀 Zero Boilerplate

Focus on your data model, not protocol details:

- **Automatic Tool Generation**: Decorators handle all MCP setup
- **Smart Defaults**: Sensible conventions out of the box
- **Clean APIs**: Intuitive patterns inspired by GraphQL and ORMs
- **Mutable Fields**: Opt‑in mutability with auto-generated patch models

## How It Works

1. **Define Your Model**: Use Pydantic models with the `@app.entity` decorator
2. **Add Relationships**: Connect entities with typed relationships
3. **Implement Resolvers**: Define how relationships load data
4. **Create Resources**: Add entry points for AI agents
5. **Run**: Start your MCP server

AI agents can then:
- Call `explore_data_model()` to understand your schema
- Use resources to access data
- Follow relationships to traverse your data graph
- All with full type safety and validation

## Installation

```bash
pip install enrichmcp
```

## Next Steps

- Follow the [Getting Started](getting-started.md) guide
- Learn about [Core Concepts](concepts.md)
- Explore the [API Reference](api.md)
- Check out [Examples](https://github.com/featureform/enrichmcp/tree/main/examples)
- Learn about [SQLAlchemy integration](sqlalchemy.md)
- Read the [Development Setup](../README.md#development-setup) guide if you want to contribute

## Support

- 📖 [Documentation](https://featureform.com/enrichmcp)
- 🐛 [Issue Tracker](https://github.com/featureform/enrichmcp/issues)
- 💬 [Discussions](https://github.com/featureform/enrichmcp/discussions)
- ⭐ [Star on GitHub](https://github.com/featureform/enrichmcp)

---

Built with ❤️ by [Featureform](https://featureform.com)
