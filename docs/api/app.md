# EnrichMCP Application

## Overview

The `EnrichMCP` class is the main entry point for creating an enrichmcp application. It manages:

- Entity registration
- Resource endpoints
- Relationship resolution
- Schema introspection

## Class Reference

### `EnrichMCP(title: str, description: str)`

Creates a new enrichmcp application.

**Parameters:**
- `title`: The name of your API
- `description`: A description of what your API provides

**Example:**
```python
from enrichmcp import EnrichMCP

app = EnrichMCP(title="My API", description="API for AI agents to access my data")
```

## Methods

### `entity(cls=None, *, description=None)`

Decorator to register a Pydantic model as an entity.

**Parameters:**
- `cls`: The model class (when used without parentheses)
- `description`: Optional description override (uses docstring by default)

**Example:**
```python
@app.entity
class User(EnrichModel):
    """User in the system."""

    id: int = Field(description="User ID")
    name: str = Field(description="Username")
```

### `resource(func=None, *, name=None, description=None)`

Decorator to register a function as an MCP resource.

**Parameters:**
- `func`: The function (when used without parentheses)
- `name`: Optional name override (uses function name by default)
- `description`: Optional description override (uses docstring by default)

**Example:**
```python
@app.resource
async def list_users() -> list[User]:
    """List all users in the system."""
    return await fetch_all_users()
```

### `run(**options)`

Start the MCP server.

**Parameters:**
- `**options`: Options passed to FastMCP (transport, host, port, etc.)

**Example:**
```python
if __name__ == "__main__":
    app.run()
```

### `describe_model() -> str`

Generate a comprehensive description of the data model. This is used internally by the `explore_data_model()` resource.

**Returns:**
A formatted string containing all entities, fields, and relationships.

## Built-in Resources

### `explore_data_model()`

Every EnrichMCP application automatically provides this resource for AI agents to discover the data model.

**Example Response:**
```json
{
    "title": "My API",
    "description": "API for AI agents to access my data",
    "entity_count": 3,
    "entities": ["User", "Order", "Product"],
    "model": "# Data Model: My API\n...",
    "usage_hint": "Use the model information above..."
}
```

## Entity Registration Flow

1. **Validation**: Checks that entity has description and all fields have descriptions
2. **Registration**: Adds entity to the app's registry
3. **Relationship Setup**: Configures relationship fields for resolution

## Resource Registration Flow

1. **Validation**: Ensures resource has a description
2. **Wrapping**: Wraps function with MCP tool decorator
3. **Registration**: Makes resource available to AI agents

## Error Handling

The app validates all relationships have resolvers before starting:

```python
# This will raise ValueError on app.run()
@app.entity
class User(EnrichModel):
    orders: list[Order] = Relationship(description="User's orders")
    # Missing: @User.orders.resolver


app.run()  # ValueError: User.orders missing resolver
```

## Best Practices

1. **Create one app instance** - Share it across your modules
2. **Register entities first** - Before defining resolvers
3. **Use descriptive names** - Help AI agents understand your API
4. **Validate early** - The app catches configuration errors at startup

## Complete Example

```python
from enrichmcp import EnrichMCP, EnrichModel, Relationship
from pydantic import Field

# Create app
app = EnrichMCP(title="Bookstore API", description="API for managing books and authors")


# Define entities
@app.entity
class Author(EnrichModel):
    """Book author."""

    id: int = Field(description="Author ID")
    name: str = Field(description="Author name")

    books: list["Book"] = Relationship(description="Books by this author")


@app.entity
class Book(EnrichModel):
    """Book in the catalog."""

    id: int = Field(description="Book ID")
    title: str = Field(description="Book title")
    author_id: int = Field(description="Author ID")

    author: Author = Relationship(description="Book author")


# Define resolvers
@Author.books.resolver
async def get_author_books(author_id: int) -> list[Book]:
    """Get all books by an author."""
    # Implementation here
    return []


@Book.author.resolver
async def get_book_author(book_id: int) -> Author:
    """Get the author of a book."""
    # Implementation here
    return Author(id=1, name="Unknown")


# Define resources
@app.resource
async def list_authors() -> list[Author]:
    """List all authors."""
    # Implementation here
    return []


# Run
if __name__ == "__main__":
    app.run()
```
