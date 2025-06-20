import pytest
from pydantic import Field

from enrichmcp import (
    EnrichMCP,
    EnrichModel,
)


def test_entity_requires_description_via_parameter():
    """Test that entity requires a description via parameter."""
    app = EnrichMCP("Test API", description="Test API description")

    # Should work with a description
    @app.entity(description="Test entity description")
    class TestEntity(EnrichModel):
        id: int = Field(description="Unique identifier")
        name: str = Field(description="User's name")

    assert "TestEntity" in app.entities
    assert app.entities["TestEntity"].__doc__ == "Test entity description"


def test_entity_accepts_class_docstring():
    """Test that entity accepts a class docstring as description."""
    app = EnrichMCP("Test API", description="Test API description")

    # Should work with a class docstring
    @app.entity
    class TestEntity(EnrichModel):
        """Test entity docstring."""

        id: int = Field(description="Unique identifier")
        name: str = Field(description="User's name")

    assert "TestEntity" in app.entities
    assert app.entities["TestEntity"].__doc__ == "Test entity docstring."


def test_entity_raises_error_without_description():
    """Test that entity raises error without description."""
    app = EnrichMCP("Test API", description="Test API description")

    # Should fail without a description
    with pytest.raises(ValueError) as exc_info:

        @app.entity
        class TestEntity(EnrichModel):
            id: int = Field(description="Unique identifier")
            name: str = Field(description="User's name")

    assert "must have a description" in str(exc_info.value)
    assert "TestEntity" in str(exc_info.value)


def test_resource_requires_description_via_parameter():
    """Test that resource requires a description via parameter."""
    app = EnrichMCP("Test API", description="Test API description")

    # Should work with a description
    @app.retrieve(description="Test resource description")
    async def test_resource():
        return {"status": "ok"}

    assert "test_resource" in app.resources


def test_resource_accepts_function_docstring():
    """Test that resource accepts a function docstring as description."""
    app = EnrichMCP("Test API", description="Test API description")

    # Should work with a function docstring
    @app.retrieve()
    async def test_resource():
        """Test resource docstring."""
        return {"status": "ok"}

    assert "test_resource" in app.resources


def test_resource_raises_error_without_description():
    """Test that resource raises error without description."""
    app = EnrichMCP("Test API", description="Test API description")

    # Should fail without a description
    with pytest.raises(ValueError) as exc_info:

        @app.retrieve()
        async def test_resource():
            return {"status": "ok"}

    assert "must have a description" in str(exc_info.value)
    assert "test_resource" in str(exc_info.value)


def test_resource_with_custom_name_and_description():
    """Test resource with custom name and description."""
    app = EnrichMCP("Test API", description="Test API description")

    # Should work with custom name and description
    @app.retrieve(name="custom_name", description="Custom resource description")
    async def test_resource():
        return {"status": "ok"}

    assert "custom_name" in app.resources
    assert "test_resource" not in app.resources
