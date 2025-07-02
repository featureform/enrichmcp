import pytest
from pydantic import Field

from enrichmcp import EnrichMCP, EnrichModel


@pytest.mark.asyncio
async def test_patch_model_generation_and_mutable_fields():
    app = EnrichMCP("Test API", description="desc")

    @app.entity
    class Customer(EnrichModel):
        """Customer entity."""

        id: int = Field(description="id")
        email: str = Field(description="email", json_schema_extra={"mutable": True})
        status: str = Field(description="status", json_schema_extra={"mutable": True})

    # mutable fields detected
    assert Customer.mutable_fields() == {"email", "status"}
    assert hasattr(Customer, "PatchModel")
    patch_fields = set(Customer.PatchModel.model_fields.keys())
    assert patch_fields == {"email", "status"}


@pytest.mark.asyncio
async def test_crud_decorators_register_resources():
    app = EnrichMCP("API", description="desc")

    @app.entity
    class Item(EnrichModel):
        """Item entity."""

        id: int = Field(description="id")
        name: str = Field(description="name", json_schema_extra={"mutable": True})

    @app.create
    async def create_item(name: str) -> Item:
        """Create item."""
        return Item(id=1, name=name)

    @app.update
    async def update_item(item_id: int, patch: Item.PatchModel) -> Item:
        """Update item."""
        return Item(id=item_id, name=patch.name or "n")

    @app.delete
    async def delete_item(item_id: int) -> bool:
        """Delete item."""
        return True

    assert "create_item" in app.resources
    assert "update_item" in app.resources
    assert "delete_item" in app.resources

    item = await create_item(name="x")
    assert item.name == "x"
    item = await update_item(1, Item.PatchModel(name="y"))
    assert item.name == "y"
    assert await delete_item(1) is True
