# Relationships

## Overview

Relationships define how entities connect to each other in your data model. They enable AI agents to traverse your data graph naturally.

## The Relationship Class

### `Relationship(*, description: str)`

Creates a relationship field on an entity.

**Parameters:**
- `description`: Required description of the relationship

**Example:**
```python
from enrichmcp import Relationship


class User(EnrichModel):
    orders: list["Order"] = Relationship(description="Orders placed by this user")
```

## Relationship Types

### One-to-One

A single related entity:

```python
@app.entity
class User(EnrichModel):
    """User account."""

    id: int = Field(description="User ID")

    profile: "UserProfile" = Relationship(description="User's profile information")


@app.entity
class UserProfile(EnrichModel):
    """User profile details."""

    user_id: int = Field(description="User ID")
    bio: str = Field(description="Biography")
```

### One-to-Many

A list of related entities:

```python
@app.entity
class Author(EnrichModel):
    """Book author."""

    id: int = Field(description="Author ID")

    books: list["Book"] = Relationship(description="Books by this author")


@app.entity
class Book(EnrichModel):
    """Published book."""

    id: int = Field(description="Book ID")
    author_id: int = Field(description="Author ID")
```

## Defining Resolvers

Every relationship needs a resolver function that fetches the data.

### Basic Resolver

```python
@Author.books.resolver
async def get_author_books(author_id: int) -> list["Book"]:
    """Fetch all books by an author.

    Args:
        author_id: The ID from the parent Author entity

    Returns:
        List of Book entities
    """
    # Your data fetching logic here
    books = await fetch_books_by_author(author_id)
    return [Book(**book_data) for book_data in books]
```

### Resolver Naming

The resolver decorator can be used with or without a name:

```python
# Default resolver (no name)
@Product.reviews.resolver
async def get_reviews(product_id: int) -> list["Review"]:
    """Get all reviews."""
    return await fetch_reviews(product_id)


# Named resolver
@Product.reviews.resolver(name="recent")
async def get_recent_reviews(product_id: int) -> list["Review"]:
    """Get recent reviews only."""
    return await fetch_recent_reviews(product_id)
```

## Type Safety

Resolver return types must match the relationship field type exactly:

```python
# Relationship expects list["Order"]
orders: list["Order"] = Relationship(...)


# ✅ Correct - matches exactly
@User.orders.resolver
async def get_orders(user_id: int) -> list["Order"]:
    return []


# ❌ Wrong - different type
@User.orders.resolver
async def bad_resolver(user_id: int) -> list[dict]:
    return []


# ❌ Wrong - Optional not allowed
@User.orders.resolver
async def bad_optional(user_id: int) -> list["Order"] | None:
    return None
```

## Resolver Arguments

Resolvers receive the parent entity's ID as their first argument:

```python
@app.entity
class Order(EnrichModel):
    """Order entity."""

    id: int = Field(description="Order ID")
    customer_id: int = Field(description="Customer ID")

    customer: "Customer" = Relationship(description="Customer who placed the order")


@Order.customer.resolver
async def get_order_customer(order_id: int) -> "Customer":
    """
    The resolver receives order_id (from Order.id),
    not customer_id, even though that's what we need.
    """
    # First get the order to find customer_id
    order = await fetch_order(order_id)
    # Then fetch the customer
    return await fetch_customer(order.customer_id)
```

## Resolver Registration

Resolvers are automatically registered as MCP resources with names following the pattern:
- `get_{entity}_{relationship}` for default resolvers
- `get_{entity}_{relationship}_{name}` for named resolvers

Examples:
- `@User.orders.resolver` → `get_user_orders`
- `@Product.reviews.resolver(name="recent")` → `get_product_reviews_recent`

## Best Practices

### 1. Handle Missing Data Gracefully

```python
@Order.customer.resolver
async def get_customer(order_id: int) -> "Customer":
    """Get customer with fallback."""
    customer = await fetch_customer_by_order(order_id)
    if not customer:
        # Return a sensible default
        return Customer(id=-1, name="Unknown Customer", email="unknown@example.com")
    return customer
```

### 2. Keep Resolvers Simple

```python
# ✅ Good - single responsibility
@Author.books.resolver
async def get_books(author_id: int) -> list["Book"]:
    """Just fetch books."""
    return await fetch_author_books(author_id)


# ❌ Avoid - doing too much
@Author.books.resolver
async def get_books_complex(author_id: int) -> list["Book"]:
    """Don't do this."""
    # Fetching extra data
    author = await fetch_author(author_id)
    # Complex business logic
    if author.is_premium:
        books = await fetch_all_books(author_id)
    else:
        books = await fetch_published_books(author_id)
    # Sorting and filtering
    books = sorted(books, key=lambda b: b.date)
    return books[:10]
```

### 3. Document Thoroughly

```python
@Customer.orders.resolver
async def get_customer_orders(customer_id: int) -> list["Order"]:
    """Get all orders for a customer.

    Retrieves the complete order history for a customer,
    including cancelled and refunded orders. Orders are
    returned in reverse chronological order (newest first).

    Args:
        customer_id: The customer's unique identifier

    Returns:
        List of Order objects, empty list if no orders

    Note:
        This includes ALL orders regardless of status
    """
    return await fetch_customer_orders(customer_id)
```

## Complete Example

```python
from enrichmcp import EnrichMCP, EnrichModel, Relationship
from pydantic import Field

app = EnrichMCP("Blog API", "Blog with posts and comments")


@app.entity
class Author(EnrichModel):
    """Blog post author."""

    id: int = Field(description="Author ID")
    name: str = Field(description="Author name")

    posts: list["Post"] = Relationship(description="Posts written by this author")


@app.entity
class Post(EnrichModel):
    """Blog post."""

    id: int = Field(description="Post ID")
    title: str = Field(description="Post title")
    author_id: int = Field(description="Author ID")

    author: "Author" = Relationship(description="Post author")
    comments: list["Comment"] = Relationship(description="Comments on this post")


@app.entity
class Comment(EnrichModel):
    """Comment on a post."""

    id: int = Field(description="Comment ID")
    post_id: int = Field(description="Post ID")
    content: str = Field(description="Comment text")

    post: "Post" = Relationship(description="Post this comment belongs to")


# Define all resolvers
@Author.posts.resolver
async def get_author_posts(author_id: int) -> list["Post"]:
    """Get all posts by an author."""
    # Implementation
    return []


@Post.author.resolver
async def get_post_author(post_id: int) -> "Author":
    """Get the author of a post."""
    # Implementation
    return Author(id=1, name="Unknown")


@Post.comments.resolver
async def get_post_comments(post_id: int) -> list["Comment"]:
    """Get all comments on a post."""
    # Implementation
    return []


@Comment.post.resolver
async def get_comment_post(comment_id: int) -> "Post":
    """Get the post a comment belongs to."""
    # Implementation
    return Post(id=1, title="Unknown", author_id=1)
```
