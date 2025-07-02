from unittest.mock import patch

import pytest
from pydantic import Field

from enrichmcp import (
    EnrichContext,
    EnrichMCP,
    EnrichModel,
)


@pytest.mark.asyncio
async def test_app_entity_decorator():
    """Test app.entity decorator."""
    app = EnrichMCP("Test API", description="Test API description")

    @app.entity(description="Test entity")
    class TestEntity(EnrichModel):
        id: int = Field(description="Unique identifier")
        name: str = Field(description="User's name")

    # Check that the entity was registered with the app
    assert "TestEntity" in app.entities
    assert app.entities["TestEntity"] is TestEntity


@pytest.mark.asyncio
async def test_entity_decorator_without_parens():
    """Test app.entity decorator without parentheses."""
    app = EnrichMCP("Test API", description="Test API description")

    @app.entity
    class TestEntityNoParens(EnrichModel):
        """Test entity using docstring for description."""

        id: int = Field(description="Unique identifier")
        name: str = Field(description="User's name")

    # Check that the entity was registered with the app
    assert "TestEntityNoParens" in app.entities
    assert app.entities["TestEntityNoParens"] is TestEntityNoParens
    # Check that docstring is preserved
    assert TestEntityNoParens.__doc__ == "Test entity using docstring for description."


@pytest.mark.asyncio
async def test_entity_with_description():
    """Test app.entity decorator with description override."""
    app = EnrichMCP("Test API", description="Test API description")

    @app.entity(description="Custom entity description")
    class UserWithDescription(EnrichModel):
        """Original docstring that should be replaced."""

        id: int = Field(description="Unique identifier")
        name: str = Field(description="User's name")

    # Check that the entity was registered with the app
    assert "UserWithDescription" in app.entities
    assert app.entities["UserWithDescription"] is UserWithDescription

    # Check that the description was set correctly
    assert UserWithDescription.__doc__ == "Custom entity description"


@pytest.mark.asyncio
async def test_resource_decorator():
    """Test resource decorator."""
    app = EnrichMCP("Test API", description="Test API description")

    @app.retrieve(description="Get user resource")
    async def get_user(*, id: int) -> dict:
        return {"id": id, "name": "Test User"}

    # Check that the function was registered in the resources dict
    assert "get_user" in app.resources
    result = await get_user(id=1)
    assert result["id"] == 1
    assert result["name"] == "Test User"


@pytest.mark.asyncio
async def test_resource_decorator_without_parens():
    """Test resource decorator without parentheses."""
    app = EnrichMCP("Test API", description="Test API description")

    @app.retrieve
    async def get_user_no_parens(*, id: int) -> dict:
        """Get user by ID without parentheses in decorator."""
        return {"id": id, "name": "Test User"}

    # Check that the function was registered in the resources dict
    assert "get_user_no_parens" in app.resources
    result = await get_user_no_parens(id=1)
    assert result["id"] == 1
    assert result["name"] == "Test User"


@pytest.mark.asyncio
async def test_resource_decorator_empty_parens():
    """Test resource decorator with empty parentheses."""
    app = EnrichMCP("Test API", description="Test API description")

    @app.retrieve()
    async def get_user_empty_parens(*, id: int) -> dict:
        """Get user by ID with empty parentheses."""
        return {"id": id, "name": "Test User"}

    # Check that the function was registered in the resources dict
    assert "get_user_empty_parens" in app.resources
    result = await get_user_empty_parens(id=1)
    assert result["id"] == 1
    assert result["name"] == "Test User"


@pytest.mark.asyncio
async def test_resource_with_description():
    """Test resource decorator with description override."""
    app = EnrichMCP("Test API", description="Test API description")

    @app.retrieve(name="custom_name", description="Custom resource description")
    async def get_data() -> dict:
        """Original docstring that should be replaced."""
        return {"status": "ok"}

    # Check that the function was registered with the custom name
    assert "custom_name" in app.resources

    # Check that it still works
    result = await get_data()
    assert result["status"] == "ok"


@pytest.mark.asyncio
async def test_resource_without_description_fails():
    """Test that resource decorator fails without description."""
    app = EnrichMCP("Test API", description="Test API description")

    with pytest.raises(ValueError, match="must have a description"):

        @app.retrieve
        async def bad_resource():
            # No docstring, should fail
            return {"status": "ok"}


@pytest.mark.asyncio
async def test_entity_without_description_fails():
    """Test that entity decorator fails without description."""
    app = EnrichMCP("Test API", description="Test API description")

    with pytest.raises(ValueError, match="must have a description"):

        @app.entity
        class BadEntity(EnrichModel):
            # No docstring, should fail
            id: int = Field(description="ID")


def test_get_context_returns_enrich_context():
    """app.get_context should return an EnrichContext"""

    app = EnrichMCP("Test API", description="Test API description")
    ctx = app.get_context()

    assert isinstance(ctx, EnrichContext)
    assert ctx.fastmcp is app.mcp

    with pytest.raises(ValueError):
        _ = ctx.request_context


def test_get_context_propagates_errors():
    app = EnrichMCP("Test API", description="desc")

    with (
        patch.object(app.mcp, "get_context", side_effect=RuntimeError("boom")),
        pytest.raises(RuntimeError),
    ):
        app.get_context()
