"""EnrichMCP API Gateway example.

This example shows how EnrichMCP can sit in front of an existing FastAPI service
and expose an agent-friendly API. All resolvers make HTTP requests to the
backend, acting as a lightweight API gateway.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import httpx
from pydantic import Field

from enrichmcp import EnrichContext, EnrichMCP, EnrichModel, Relationship

BACKEND_URL = "http://localhost:8001"


@asynccontextmanager
async def lifespan(app: EnrichMCP) -> AsyncIterator[dict[str, Any]]:
    async with httpx.AsyncClient(base_url=BACKEND_URL) as client:
        yield {"client": client}


app = EnrichMCP(
    title="Shop API Gateway",
    description="EnrichMCP front-end for a FastAPI backend",
    lifespan=lifespan,
)


@app.entity
class User(EnrichModel):
    """Customer account."""

    id: int = Field(description="User ID")
    username: str = Field(description="Username")
    email: str = Field(description="Email")
    full_name: str = Field(description="Full name")
    created_at: datetime = Field(description="Account created")

    orders: list["Order"] = Relationship(description="Orders for the user")


@app.entity
class Product(EnrichModel):
    """Product for sale."""

    id: int = Field(description="Product ID")
    sku: str = Field(description="SKU")
    name: str = Field(description="Name")
    price: float = Field(description="Price in USD")


@app.entity
class Order(EnrichModel):
    """Customer order."""

    id: int = Field(description="Order ID")
    order_number: str = Field(description="Order number")
    user_id: int = Field(description="Owner user ID")
    created_at: datetime = Field(description="Created timestamp")
    status: str = Field(description="Status")
    total_amount: float = Field(description="Total amount")

    user: User = Relationship(description="User who placed the order")
    products: list[Product] = Relationship(description="Products in the order")


async def _client(ctx: EnrichContext) -> httpx.AsyncClient:
    """Helper to get the shared HTTP client."""
    return ctx.request_context.lifespan_context["client"]


@app.retrieve
async def list_users(ctx: EnrichContext) -> list[User]:
    """Fetch all users from the backend service."""
    client = await _client(ctx)
    resp = await client.get("/users")
    resp.raise_for_status()
    return [User(**u) for u in resp.json()]


@app.retrieve
async def get_user(user_id: int, ctx: EnrichContext) -> User:
    """Return a single user by ID."""
    client = await _client(ctx)
    resp = await client.get(f"/users/{user_id}")
    resp.raise_for_status()
    return User(**resp.json())


@app.retrieve
async def list_products(ctx: EnrichContext) -> list[Product]:
    """Retrieve all products available for sale."""
    client = await _client(ctx)
    resp = await client.get("/products")
    resp.raise_for_status()
    return [Product(**p) for p in resp.json()]


@app.retrieve
async def get_product(product_id: int, ctx: EnrichContext) -> Product:
    """Get a single product by ID."""
    client = await _client(ctx)
    resp = await client.get(f"/products/{product_id}")
    resp.raise_for_status()
    return Product(**resp.json())


@app.retrieve
async def list_orders(
    user_id: int | None = None,
    ctx: EnrichContext | None = None,
) -> list[Order]:
    """List orders optionally filtered by user."""
    if ctx is None:
        raise RuntimeError("Context required")
    client = await _client(ctx)
    params = {"user_id": user_id} if user_id is not None else None
    resp = await client.get("/orders", params=params)
    resp.raise_for_status()
    return [Order(**o) for o in resp.json()]


@app.retrieve
async def get_order(order_id: int, ctx: EnrichContext) -> Order:
    """Retrieve a specific order."""
    client = await _client(ctx)
    resp = await client.get(f"/orders/{order_id}")
    resp.raise_for_status()
    return Order(**resp.json())


@User.orders.resolver
async def get_orders_for_user(user_id: int, ctx: EnrichContext) -> list["Order"]:
    return await list_orders(user_id=user_id, ctx=ctx)


@Order.user.resolver
async def get_order_user(user_id: int, ctx: EnrichContext) -> "User":
    return await get_user(user_id=user_id, ctx=ctx)


@Order.products.resolver
async def get_order_products(order_id: int, ctx: EnrichContext) -> list[Product]:
    client = await _client(ctx)
    resp = await client.get(f"/orders/{order_id}")
    resp.raise_for_status()
    data = resp.json()
    products = []
    for pid in data.get("product_ids", []):
        r = await client.get(f"/products/{pid}")
        r.raise_for_status()
        products.append(Product(**r.json()))
    return products


if __name__ == "__main__":
    print("Starting Shop API Gateway...")
    app.run()
