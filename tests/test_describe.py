from typing import Any

import pytest
from pydantic import Field

from enrichmcp import (
    EnrichMCP,
    EnrichModel,
    Relationship,
)


def test_field_requires_description():
    """Test that entity fields require descriptions."""
    app = EnrichMCP("Test API", description="Test API description")

    # Should work with field descriptions
    @app.entity(description="User entity")
    class UserWithDescriptions(EnrichModel):
        id: int = Field(description="Unique identifier")
        name: str = Field(description="User's full name")

    assert "UserWithDescriptions" in app.entities

    # Should fail without field descriptions
    with pytest.raises(ValueError) as exc_info:

        @app.entity(description="User entity")
        class UserWithoutDescriptions(EnrichModel):
            id: int = Field()  # Missing description
            name: str = Field(description="User's full name")

    assert "must have a description" in str(exc_info.value)
    assert "id" in str(exc_info.value)


def test_describe_method():
    """Test the describe method of EnrichModel."""
    app = EnrichMCP("Test API", description="Test API description")

    @app.entity(description="User entity for testing")
    class User(EnrichModel):
        id: int = Field(description="Unique identifier")
        name: str = Field(description="User's full name")
        email: str = Field(description="User's email address")
        address: Relationship = Relationship(description="User's address")
        posts: Relationship = Relationship(description="User's blog posts")

    # Create a user instance
    user = User(id=1, name="John Doe", email="john@example.com")

    # Get the description
    description = user.describe()

    # Check the description content
    assert "# User" in description
    assert "User entity for testing" in description
    assert "## Fields" in description
    assert "**id** (int): Unique identifier" in description
    assert "**name** (str): User's full name" in description
    assert "**email** (str): User's email address" in description
    assert "## Relationships" in description
    assert "**address** → Relationship: User's address" in description
    assert "**posts** → Relationship: User's blog posts" in description


def test_describe_method_with_complex_types():
    """Test the describe method with complex field types."""
    app = EnrichMCP("Test API", description="Test API description")

    @app.entity(description="Blog post entity")
    class Post(EnrichModel):
        id: int = Field(description="Unique identifier")
        title: str = Field(description="Post title")
        tags: list[str] = Field(description="Post tags")
        metadata: dict[str, Any] = Field(description="Post metadata")
        author: Relationship = Relationship(description="Post author")

    # Create a post instance
    post = Post(id=1, title="Test Post", tags=["test", "example"], metadata={"published": True})

    # Get the description
    description = post.describe()

    # Check the description content
    assert "# Post" in description
    assert "Blog post entity" in description
    assert "**id** (int): Unique identifier" in description
    assert "**title** (str): Post title" in description
    assert "**tags** (list): Post tags" in description
    assert "**metadata** (dict): Post metadata" in description
    assert "**author** → Relationship: Post author" in description
