"""EnrichMCP API Gateway example.

This example shows how EnrichMCP can sit in front of an existing FastAPI service
and expose an agent-friendly API. All resolvers make HTTP requests to the
backend, acting as a lightweight API gateway.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING, Any

import httpx
from fastmcp import Context  # noqa: TC002
from pydantic import Field

from enrichmcp import EnrichMCP, EnrichModel, Relationship

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

BACKEND_URL = "http://localhost:8001"


@asynccontextmanager
async def lifespan(app: EnrichMCP) -> AsyncIterator[dict[str, Any]]:
    async with httpx.AsyncClient(base_url=BACKEND_URL) as client:
        yield {"client": client}


app = EnrichMCP(
    title="Shop API Gateway",
    instructions="EnrichMCP front-end for a FastAPI backend",
    lifespan=lifespan,
)


@app.entity()
class User(EnrichModel):
    """Customer account."""

    id: int = Field(description="User ID")
    username: str = Field(description="Username")
    email: str = Field(description="Email")
    full_name: str = Field(description="Full name")
    created_at: datetime = Field(description="Account created")

    orders: list[Order] = Relationship(description="Orders for the user")


@app.entity()
class Product(EnrichModel):
    """Product for sale."""

    id: int = Field(description="Product ID")
    sku: str = Field(description="SKU")
    name: str = Field(description="Name")
    price: float = Field(description="Price in USD")


@app.entity()
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


@app.retrieve()
async def list_users(ctx: Context) -> list[User]:
    """Fetch all users from the backend service."""
    client = ctx.request_context.lifespan_context["client"]
    resp = await client.get("/users")
    resp.raise_for_status()
    return [User(**u) for u in resp.json()]


@app.retrieve()
async def get_user(user_id: int, ctx: Context) -> User:
    """Return a single user by ID."""
    client = ctx.request_context.lifespan_context["client"]
    resp = await client.get(f"/users/{user_id}")
    resp.raise_for_status()
    return User(**resp.json())


@app.retrieve()
async def list_products(ctx: Context) -> list[Product]:
    """Retrieve all products available for sale."""
    client = ctx.request_context.lifespan_context["client"]
    resp = await client.get("/products")
    resp.raise_for_status()
    return [Product(**p) for p in resp.json()]


@app.retrieve()
async def get_product(product_id: int, ctx: Context) -> Product:
    """Get a single product by ID."""
    client = ctx.request_context.lifespan_context["client"]
    resp = await client.get(f"/products/{product_id}")
    resp.raise_for_status()
    return Product(**resp.json())


@app.retrieve()
async def list_orders(
    ctx: Context,
    user_id: int | None = None,
) -> list[Order]:
    """List orders optionally filtered by user."""
    client = ctx.request_context.lifespan_context["client"]
    params = {"user_id": user_id} if user_id is not None else None
    resp = await client.get("/orders", params=params)
    resp.raise_for_status()
    return [Order(**o) for o in resp.json()]


@app.retrieve()
async def get_order(order_id: int, ctx: Context) -> Order:
    """Retrieve a specific order."""
    client = ctx.request_context.lifespan_context["client"]
    resp = await client.get(f"/orders/{order_id}")
    resp.raise_for_status()
    return Order(**resp.json())


@User.orders.resolver
async def get_orders_for_user(user_id: int, ctx: Context) -> list[Order]:
    return await list_orders(ctx, user_id=user_id)


@Order.user.resolver
async def get_order_user(user_id: int, ctx: Context) -> User:
    return await get_user(user_id=user_id, ctx=ctx)


@Order.products.resolver
async def get_order_products(order_id: int, ctx: Context) -> list[Product]:
    client = ctx.request_context.lifespan_context["client"]
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
