# Getting Started

This guide will help you get up and running with enrichmcp in minutes.

## Installation

Install enrichmcp using pip:

```bash
pip install enrichmcp
```

Or if you're using Poetry:

```bash
poetry add enrichmcp
```

## Basic Concepts

enrichmcp is built around three core concepts:

### 1. Entities

Entities are Pydantic models that represent your domain objects. They're decorated with `@app.entity` and include rich descriptions for AI agents:

```python
@app.entity
class Product(EnrichModel):
    """Represents a product in the catalog."""

    id: int = Field(description="Unique product identifier")
    name: str = Field(description="Product display name")
    price: float = Field(description="Current price in USD")
```

### 2. Relationships

Relationships connect entities together, allowing AI agents to traverse your data graph:

```python
@app.entity
class Order(EnrichModel):
    """Customer order containing products."""

    id: int = Field(description="Order ID")

    # Define relationships
    customer: Customer = Relationship(description="Customer who placed this order")
    products: list[Product] = Relationship(description="Products in this order")
```

### 3. Resolvers

Resolvers define how relationships are fetched from your data source:

```python
@Order.customer.resolver
async def get_order_customer(order_id: int) -> Customer:
    """Fetch the customer for an order."""
    # Your database logic here
    return await db.get_customer_by_order(order_id)
```

## Your First API

Let's build a simple book catalog API:

```python
from datetime import date
from enrichmcp import EnrichMCP, EnrichModel, Relationship
from pydantic import Field

# Create the application
app = EnrichMCP(title="Book Catalog API", description="A simple book catalog for AI agents")


# Define entities
@app.entity
class Author(EnrichModel):
    """Represents a book author."""

    id: int = Field(description="Author ID")
    name: str = Field(description="Author's full name")
    bio: str = Field(description="Short biography")

    # Relationship to books
    books: list["Book"] = Relationship(description="Books written by this author")


@app.entity
class Book(EnrichModel):
    """Represents a book in the catalog."""

    id: int = Field(description="Book ID")
    title: str = Field(description="Book title")
    isbn: str = Field(description="ISBN-13")
    published: date = Field(description="Publication date")
    author_id: int = Field(description="Author ID")

    # Relationship to author
    author: Author = Relationship(description="Author of this book")


# Define resolvers
@Author.books.resolver
async def get_author_books(author_id: int) -> list[Book]:
    """Get all books by an author."""
    # In real app, this would query a database
    return [
        Book(
            id=1,
            title="Example Book",
            isbn="978-0-123456-78-9",
            published=date(2023, 1, 1),
            author_id=author_id,
        )
    ]


@Book.author.resolver
async def get_book_author(book_id: int) -> Author:
    """Get the author of a book."""
    # In real app, this would query a database
    return Author(id=1, name="Jane Doe", bio="Bestselling author")


# Define root resources
@app.resource
async def list_books() -> list[Book]:
    """List all books in the catalog."""
    return [
        Book(
            id=1,
            title="Example Book",
            isbn="978-0-123456-78-9",
            published=date(2023, 1, 1),
            author_id=1,
        )
    ]


@app.resource
async def get_author(author_id: int) -> Author:
    """Get a specific author by ID."""
    return Author(id=author_id, name="Jane Doe", bio="Bestselling author")


# Run the server
if __name__ == "__main__":
    app.run()
```

## Next Steps

- Explore more [Examples](examples.md)
- Read about [Core Concepts](concepts.md)
- Check the [API Reference](api.md)
