# ruff: noqa: UP007
"""
Tests for relationship type validation and edge cases.
"""

from typing import Any, Optional, Union

from pydantic import Field

from enrichmcp import EnrichMCP
from enrichmcp.entity import EnrichModel
from enrichmcp.relationship import Relationship


def test_type_compatibility():
    """Test type compatibility checking with different type annotations."""
    # Create a relationship instance
    rel = Relationship(description="Test relationship")

    # Test simple type compatibility
    assert rel._is_compatible_type(str, str) is True

    # Test compatibility with string types
    assert rel._is_compatible_type("User", "User") is True

    # Test Union compatibility - both traditional and pipe syntax should work
    # This is now handled directly by _is_compatible_type
    # Optional should be compatible with its inner type
    assert rel._is_compatible_type(Optional[str], str) is True
    # Pipe syntax Optional
    assert rel._is_compatible_type(str | None, str) is True

    # Test Optional type compatibility
    # Same Optional types
    assert rel._is_compatible_type(Optional[str], Optional[str]) is True
    # Different syntax but same meaning
    assert rel._is_compatible_type(str | None, Optional[str]) is True
    assert rel._is_compatible_type(Optional[str], str | None) is True

    # Test compatibility between different Union types
    # Same Union types
    assert rel._is_compatible_type(Union[str, int], Union[str, int]) is True
    # Different syntax but same meaning
    assert rel._is_compatible_type(str | int, Union[str, int]) is True
    assert rel._is_compatible_type(Union[str, int], str | int) is True

    # Test inheritance compatibility
    class Parent:
        pass

    class Child(Parent):
        pass

    assert rel._is_compatible_type(Child, Parent) is True


def test_relationship_is_compatible_type():
    """Test type compatibility checking."""
    # Create a relationship instance
    rel = Relationship(description="Test relationship")

    # Test string types (can't be checked at runtime)
    assert rel._is_compatible_type("User", "User") is True
    assert rel._is_compatible_type(str, "User") is True

    # Test subclass relationship
    class Parent:
        pass

    class Child(Parent):
        pass

    assert rel._is_compatible_type(Child, Parent) is True

    # Test non-type objects (should return True for safety)
    assert rel._is_compatible_type(5, "not_a_type") is True

    # Test direct equality
    assert rel._is_compatible_type(str, str) is True


def test_resolver_with_missing_types():
    """Test resolvers with missing type annotations."""
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

    # Test function without return type annotation
    @User.items.resolver
    async def get_items_no_return(user_id: int):
        # No return type annotation
        return [Item(id=1, name="Test Item")]

    # Access the relationship directly for testing
    relationship = User.items

    # Test with no target type
    original_target_type = relationship.target_type
    relationship.target_type = None

    @User.items.resolver(name="no_target_type")
    async def get_items_no_target(user_id: int) -> list[Item]:
        return [Item(id=1, name="Test Item")]

    # Restore the original target type
    relationship.target_type = original_target_type


def test_resolver_with_string_types():
    """Test resolvers with string type annotations."""
    app = EnrichMCP(title="Test API", description="Test API for string types")

    # Define entity with string type annotation
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

        # Using string type annotation
        items: "list[Item]" = Relationship(description="User's items with string type")

    # This should work - resolvers should handle string type annotations
    @User.items.resolver
    async def get_items_string_type(user_id: int) -> list[Item]:
        return [Item(id=1, name="Test Item")]


def test_resolver_with_union_type():
    """Test resolvers with Union type annotations."""
    app = EnrichMCP(title="Test API", description="Test API for Union types")

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

        # Using Union type with pipe syntax
        items: list[Item] | None = Relationship(description="User's items with Union")

    # Test with Union return type
    @User.items.resolver
    async def get_items_union(user_id: int) -> list[Item] | dict[str, Any]:
        if user_id > 0:
            return [Item(id=1, name="Test Item")]
        return {"default": Item(id=0, name="Default Item")}
