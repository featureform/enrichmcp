# API Reference

This section provides detailed documentation for all enrichmcp components.

## Core Components

### [EnrichMCP](api/app.md)
The main application class that manages entities, relationships, and resources.

```python
from enrichmcp import EnrichMCP

app = EnrichMCP(title="My API", description="API for AI agents")
```

### [EnrichModel](api/entity.md)
Base class for all entities, extending Pydantic's BaseModel with relationship support.

```python
from enrichmcp import EnrichModel
from pydantic import Field


@app.entity
class User(EnrichModel):
    id: int = Field(description="User ID")
    name: str = Field(description="Username")
```

### [Relationship](api/relationship.md)
Defines connections between entities with automatic resolver registration.

```python
from enrichmcp import Relationship


class User(EnrichModel):
    orders: list["Order"] = Relationship(description="User's orders")
```

### [EnrichContext](api/context.md)
Context object with request scoped utilities including caching.

### [EnrichParameter](api/parameter.md)
Attach metadata like descriptions and examples to function parameters.

### [Cache](api/cache.md)
Request, user, and global scoped caching utilities.

### [Errors](api/errors.md)
Currently uses standard Python exceptions and Pydantic validation.

## Key Concepts

### Entity Registration
Entities must be registered with the app using the `@app.entity` decorator:

```python
@app.entity
class Product(EnrichModel):
    """Product in our catalog."""

    id: int = Field(description="Product ID")
    name: str = Field(description="Product name")
```

### Relationship Resolution
Every relationship needs a resolver function:

```python
@User.orders.resolver
async def get_user_orders(user_id: int) -> list["Order"]:
    """Fetch orders for a user."""
    return fetch_orders_for_user(user_id)
```

### Resource Creation
Resources are the entry points for AI agents:

```python
@app.retrieve
async def list_users() -> list[User]:
    """List all users in the system."""
    return fetch_all_users()
```

## Type Safety

enrichmcp enforces strict type checking:

1. **Entity Validation**: All fields must have descriptions
2. **Resolver Validation**: Return types must match relationship types exactly
3. **Runtime Validation**: Pydantic validates all data at runtime

## Schema Introspection

AI agents can explore your data model using the built-in `explore_data_model()` resource:

```python
# Automatically available to AI agents
result = await explore_data_model()
# Returns comprehensive schema information
```

## Best Practices

1. **Always include descriptions** - Every entity, field, and relationship needs a description
2. **Use meaningful names** - Clear, descriptive names help AI agents understand your model
3. **Keep resolvers simple** - Each resolver should do one thing well
4. **Handle missing data gracefully** - Return sensible defaults rather than errors when possible
