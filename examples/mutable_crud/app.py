from datetime import datetime

from pydantic import Field

from enrichmcp import EnrichMCP, EnrichModel, EnrichParameter

app = EnrichMCP(
    title="Customer CRUD API",
    description="Demonstrates mutability and CRUD decorators",
)


@app.entity
class Customer(EnrichModel):
    """Simple customer record."""

    id: int = Field(description="Customer ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    email: str = Field(json_schema_extra={"mutable": True}, description="Email address")
    tier: str = Field(
        json_schema_extra={"mutable": True}, description="Subscription tier", default="free"
    )


CUSTOMERS: dict[int, Customer] = {}


@app.create
async def create_customer(
    email: str = EnrichParameter(description="Customer email"),
    tier: str = EnrichParameter(default="free", description="Subscription tier"),
) -> Customer:
    """Create a new customer."""
    cid = len(CUSTOMERS) + 1
    customer = Customer(id=cid, email=email, tier=tier)
    CUSTOMERS[cid] = customer
    return customer


@app.update
async def update_customer(
    customer_id: int = EnrichParameter(description="Customer ID"),
    patch: Customer.PatchModel = EnrichParameter(description="Mutable fields to update"),  # noqa: B008
) -> Customer:
    """Update an existing customer."""
    customer = CUSTOMERS[customer_id]
    data = patch.dict(exclude_unset=True)
    updated = customer.copy(update=data)
    CUSTOMERS[customer_id] = updated
    return updated


@app.delete
async def delete_customer(
    customer_id: int = EnrichParameter(description="Customer ID"),
) -> bool:
    """Delete a customer."""
    return CUSTOMERS.pop(customer_id, None) is not None


def main() -> None:
    app.run()


if __name__ == "__main__":
    main()
