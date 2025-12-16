"""Redis Shop API Example for EnrichMCP.

This example shows how to use the Redis integration after it's implemented.
Demonstrates practical indexing with minimal complexity - only search what you need.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from pydantic import Field as PydanticField

# Add src directory to path for imports when running as standalone script
if __name__ == "__main__":
    src_path = Path(__file__).resolve().parents[2] / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

# Import the Redis integration
from enrichmcp.redis import EnrichMCP, EnrichModel, Field, Relationship

# Create Redis-enabled app
app = EnrichMCP(
    title="Redis E-Commerce Shop API",
    instructions="E-commerce API with Redis search capabilities.",
    redis_url="redis://localhost:6379",
)


# Define entities with minimal, practical indexing
@app.entity()
class User(EnrichModel):
    """Customer account with search capabilities."""

    id: int = Field(description="Unique user identifier", index="primary")

    # Searchable fields - only what you'd actually search for
    username: str = Field(description="Username for login", index="text")
    email: str = Field(description="Email address", index="text")
    full_name: str = Field(description="Customer's full name", index="text")
    account_status: str = Field(description="Status: active, suspended, flagged", index="tag")
    risk_score: float = Field(description="Risk score 0.0-1.0", index="numeric")

    # Regular fields - not indexed, just stored
    phone: str = Field(description="Contact phone number")
    created_at: datetime | None = Field(description="Account creation timestamp", default=None)
    total_spent: float = Field(description="Lifetime purchase amount")
    billing_address: str = Field(description="Default billing address")


@app.entity()
class Product(EnrichModel):
    """Product with search capabilities."""

    id: int = Field(description="Unique product identifier", index="primary")

    # Searchable fields
    name: str = Field(description="Product name", index="text")
    category: str = Field(description="Product category", index="tag")
    price: float = Field(description="Price in USD", index="numeric")

    # Regular fields
    sku: str = Field(description="Stock keeping unit")
    description: str = Field(description="Product description")
    stock: int = Field(description="Available inventory")
    is_active: bool = Field(description="Whether available for sale")
    fraud_risk: str = Field(description="Fraud risk level: low, medium, high")


@app.entity()
class Order(EnrichModel):
    """Order with search capabilities."""

    id: int = Field(description="Unique order identifier", index="primary")

    # Foreign key fields that are also searchable
    user_id: int = Field(description="Customer ID", index="tag")

    # Other searchable fields
    status: str = Field(description="Order status", index="tag")
    total_amount: float = Field(description="Total value", index="numeric")

    # Regular fields
    order_number: str = Field(description="Human-readable order number")
    created_at: datetime | None = Field(description="Order timestamp", default=None)
    payment_method: str = Field(description="Payment type")
    billing_address: str = Field(description="Billing address")
    risk_score: float = Field(description="Calculated risk score")
    product_ids: list[int] = PydanticField(
        description="List of product IDs in this order", default_factory=list
    )

    # Relationships
    user: User = Relationship(description="Customer who placed order", source_field="user_id")
    products: list[Product] = Relationship(
        description="Products in order",
        source_field="product_ids",  # Assuming we store product IDs array
    )


# Sample data
SAMPLE_USERS = [
    {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "full_name": "John Doe",
        "account_status": "active",
        "risk_score": 0.1,
        "phone": "+1-555-0123",
        "created_at": datetime(2022, 1, 15),
        "total_spent": 2547.93,
        "billing_address": "123 Main St, Anytown, NY 12345",
    },
    {
        "id": 2,
        "username": "jane_smith",
        "email": "jane@example.com",
        "full_name": "Jane Smith",
        "account_status": "active",
        "risk_score": 0.05,
        "phone": "+1-555-0124",
        "created_at": datetime(2021, 6, 20),
        "total_spent": 5832.17,
        "billing_address": "456 Oak Ave, Somewhere, CA 90210",
    },
    {
        "id": 3,
        "username": "suspicious_user",
        "email": "temp@protonmail.com",
        "full_name": "Alex Johnson",
        "account_status": "flagged",
        "risk_score": 0.85,
        "phone": "+1-555-9999",
        "created_at": datetime(2024, 1, 5),
        "total_spent": 4299.99,
        "billing_address": "789 Suspicious Lane, Newark, NJ 07101",
    },
]

SAMPLE_PRODUCTS = [
    {
        "id": 101,
        "name": "Smartphone Pro",
        "category": "Electronics",
        "price": 999.99,
        "sku": "PHONE-001",
        "description": "Latest model smartphone with 256GB storage",
        "stock": 45,
        "is_active": True,
        "fraud_risk": "high",
    },
    {
        "id": 102,
        "name": "Running Shoes",
        "category": "Footwear",
        "price": 149.99,
        "sku": "SHOE-001",
        "description": "Professional running shoes with advanced cushioning",
        "stock": 120,
        "is_active": True,
        "fraud_risk": "low",
    },
]

SAMPLE_ORDERS = [
    {
        "id": 1001,
        "user_id": 1,
        "status": "delivered",
        "total_amount": 149.99,
        "order_number": "ORD-2023-1001",
        "created_at": datetime(2023, 10, 15),
        "payment_method": "credit_card",
        "billing_address": "123 Main St, Anytown, NY 12345",
        "risk_score": 0.1,
        "product_ids": [102],
    },
    {
        "id": 1002,
        "user_id": 3,
        "status": "flagged",
        "total_amount": 4299.99,
        "order_number": "ORD-2024-1002",
        "created_at": datetime(2024, 1, 6),
        "payment_method": "credit_card",
        "billing_address": "789 Suspicious Lane, Newark, NJ 07101",
        "risk_score": 0.95,
        "product_ids": [101, 101, 101],  # Multiple expensive phones
    },
]

# Redis Storage Structure:
#
# Documents stored as JSON with prefixed keys:
# - "user:1" -> {"username": "john_doe", "email": "john@example.com", ...}
# - "product:101" -> {"name": "Smartphone Pro", "category": "Electronics", ...}
# - "order:1001" -> {"user_id": 1, "status": "delivered", "product_ids": [102], ...}
#
# Indices created automatically:
# - user_idx: PREFIX "user:" with text/tag/numeric fields
# - product_idx: PREFIX "product:" with text/tag/numeric fields
# - order_idx: PREFIX "order:" with tag/numeric fields
#
# The Redis integration would auto-generate these MCP resources:
#
# Text Search:
# - search_user_by_text(query: str) -> list[User]
# - search_product_by_text(query: str) -> list[Product]
#
# Tag Filtering:
# - filter_user_by_account_status(status: str) -> list[User]
# - filter_product_by_category(category: str) -> list[Product]
# - filter_order_by_status(status: str) -> list[Order]
# - find_orders_by_user_id(user_id: int) -> list[Order]
#
# Numeric Range:
# - find_users_by_risk_score_range(min_score: float, max_score: float) -> list[User]
# - find_products_by_price_range(min_price: float, max_price: float) -> list[Product]
# - find_orders_by_amount_range(min_amount: float, max_amount: float) -> list[Order]
#
# Primary Key Lookup:
# - get_user_by_id(id: int) -> User
# - get_product_by_id(id: int) -> Product
# - get_order_by_id(id: int) -> Order


async def setup_sample_data():
    """Set up Redis indices and populate sample data."""
    print("🚀 Starting Redis E-Commerce Shop API...")
    redis_url = app.redis_backend.redis_url
    print(f"📡 Connecting to Redis at {redis_url}")
    print("💡 Make sure Redis Stack is running: docker-compose up -d")
    print()

    # Create indices for all registered models
    for model_name, model_class in app._redis_models.items():
        await app._create_model_index(model_name, model_class)

    # Populate sample data
    await app.redis_backend.populate_sample_data(
        {"users": SAMPLE_USERS, "products": SAMPLE_PRODUCTS, "orders": SAMPLE_ORDERS}
    )

    print("💾 Sample data loaded successfully!")
    print()
    print("🎯 MCP server ready! Connect your AI agent to start searching.")


# Set up startup lifespan to handle sample data
app.lifespan = setup_sample_data

if __name__ == "__main__":
    # Start the MCP server (data setup happens automatically via lifespan)
    app.run()
