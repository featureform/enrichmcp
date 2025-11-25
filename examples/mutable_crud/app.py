"""Mutable CRUD example for EnrichMCP.

This example demonstrates how to create, update, and delete entities
with mutable fields using EnrichMCP.
"""

from datetime import UTC, datetime

from pydantic import Field

from enrichmcp import EnrichMCP, EnrichModel

app = EnrichMCP(
    title="Customer CRUD API",
    instructions="Demonstrates mutability and CRUD decorators",
)


@app.entity()
class Customer(EnrichModel):
    """Simple customer record."""

    id: int = Field(description="Customer ID")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Creation timestamp"
    )
    email: str = Field(json_schema_extra={"mutable": True}, description="Email address")
    tier: str = Field(
        json_schema_extra={"mutable": True},
        description="Subscription tier",
        default="free",
    )


CUSTOMERS: dict[int, Customer] = {}


@app.create()
async def create_customer(email: str, tier: str = "free") -> Customer:
    """Create a new customer."""
    cid = len(CUSTOMERS) + 1
    customer = Customer(id=cid, email=email, tier=tier)
    CUSTOMERS[cid] = customer
    return customer


@app.update()
async def update_customer(customer_id: int, patch: Customer.PatchModel) -> Customer:
    """Update an existing customer."""
    customer = CUSTOMERS[customer_id]
    data = patch.dict(exclude_unset=True)
    updated = customer.copy(update=data)
    CUSTOMERS[customer_id] = updated
    return updated


@app.delete()
async def delete_customer(customer_id: int) -> bool:
    """Delete a customer."""
    return CUSTOMERS.pop(customer_id, None) is not None


def main() -> None:
    """Run the mutable CRUD API server."""
    app.run()


if __name__ == "__main__":
    main()
