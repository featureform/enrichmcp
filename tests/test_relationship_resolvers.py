"""
Tests for relationship resolver type validation.
"""

import pytest
from pydantic import Field

from enrichmcp import EnrichMCP
from enrichmcp.entity import EnrichModel
from enrichmcp.relationship import Relationship


def test_relationship_resolver_type_validation():
    """Test that relationship resolver type validation works correctly."""

    app = EnrichMCP(title="Test API", description="Test API for type validation")

    @app.entity
    class Item(EnrichModel):
        """Test item entity."""

        id: int = Field(description="Item ID")
        name: str = Field(description="Item name")

    @app.entity
    class User(EnrichModel):
        """Test user entity."""

        id: int = Field(description="User ID")
        name: str = Field(description="User name")

        # Define relationship with correct type annotation
        items: list[Item] = Relationship(description="User's items")

    # This should work - correct return type
    @User.items.resolver
    async def get_items(user_id: int) -> list[Item]:
        return [Item(id=1, name="Test Item")]

    # This should fail - incorrect return type
    with pytest.raises(TypeError):

        @User.items.resolver(name="get_wrong_type")
        async def get_wrong_type(user_id: int) -> list[str]:
            return ["Not an item"]

    # This should work - Optional return type
    @User.items.resolver(name="get_optional")
    async def get_optional(user_id: int) -> list[Item] | None:
        if user_id > 0:
            return [Item(id=1, name="Test Item")]
        return None

    # This should work - Union return type
    @User.items.resolver(name="get_union")
    async def get_union(user_id: int) -> list[Item] | dict[str, Item]:
        if user_id > 0:
            return [Item(id=1, name="Test Item")]
        return {"default": Item(id=0, name="Default Item")}


def test_unresolved_relationship_validation():
    """Test that app.run() fails if a relationship is missing a resolver."""

    app = EnrichMCP(title="Test API", description="Test API for relationship validation")

    @app.entity
    class Item(EnrichModel):
        """Test item entity."""

        id: int = Field(description="Item ID")
        name: str = Field(description="Item name")

    @app.entity
    class User(EnrichModel):
        """Test user entity."""

        id: int = Field(description="User ID")
        name: str = Field(description="User name")

        # Define relationship but don't add a resolver
        items: list[Item] = Relationship(description="User's items")

    # This should fail because the relationship has no resolver
    with pytest.raises(ValueError) as excinfo:
        app.run()

    # Check that the error message is correct
    assert "User.items" in str(excinfo.value)
    assert "missing resolvers" in str(excinfo.value)
