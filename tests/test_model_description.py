from typing import Any

from pydantic import Field

from enrichmcp import (
    EnrichMCP,
    EnrichModel,
    Relationship,
)


def test_describe_model_empty():
    """Test describe_model with no entities."""
    app = EnrichMCP("Test API", description="Test API description")

    # Get the model description
    description = app.describe_model()

    # Check the description content
    assert "# Data Model: Test API" in description
    assert "Test API description" in description
    assert "*No entities registered*" in description


def test_describe_model_with_entities():
    """Test describe_model with multiple entities and relationships."""
    app = EnrichMCP("Social Network", description="A social network data model")

    # Define some entities
    @app.entity(description="User entity for the social network")
    class User(EnrichModel):
        id: int = Field(description="Unique identifier")
        name: str = Field(description="User's full name")
        email: str = Field(description="User's email address")
        is_active: bool = Field(description="Whether the user is active")

        # Relationships
        posts: Relationship = Relationship(description="User's posts")
        followers: Relationship = Relationship(description="User's followers")

    @app.entity(description="Post entity for the social network")
    class Post(EnrichModel):
        id: int = Field(description="Unique identifier")
        title: str = Field(description="Post title")
        content: str = Field(description="Post content")
        published: bool = Field(description="Whether the post is published")

        # Relationships
        author: Relationship = Relationship(description="Post author")
        comments: Relationship = Relationship(description="Comments on the post")

    @app.entity(description="Comment entity for the social network")
    class Comment(EnrichModel):
        id: int = Field(description="Unique identifier")
        content: str = Field(description="Comment content")

        # Relationships
        author: Relationship = Relationship(description="Comment author")
        post: Relationship = Relationship(description="Post being commented on")

    # Get the model description
    description = app.describe_model()

    # Check the title and table of contents
    assert "# Data Model: Social Network" in description
    assert "A social network data model" in description
    assert "## Entities" in description
    assert "- [Comment](#comment)" in description
    assert "- [Post](#post)" in description
    assert "- [User](#user)" in description

    # Check User entity description
    assert "## User" in description
    assert "User entity for the social network" in description
    assert "### Fields" in description
    assert "- **id** (int): Unique identifier" in description
    assert "- **name** (str): User's full name" in description
    assert "- **email** (str): User's email address" in description
    assert "- **is_active** (bool): Whether the user is active" in description
    assert "### Relationships" in description
    assert "- **posts** → Relationship: User's posts" in description
    assert "- **followers** → Relationship: User's followers" in description

    # Check Post entity description
    assert "## Post" in description
    assert "Post entity for the social network" in description
    assert "- **id** (int): Unique identifier" in description
    assert "- **title** (str): Post title" in description
    assert "- **content** (str): Post content" in description
    assert "- **published** (bool): Whether the post is published" in description
    assert "- **author** → Relationship: Post author" in description
    assert "- **comments** → Relationship: Comments on the post" in description

    # Check Comment entity description
    assert "## Comment" in description
    assert "Comment entity for the social network" in description
    assert "- **id** (int): Unique identifier" in description
    assert "- **content** (str): Comment content" in description
    assert "- **author** → Relationship: Comment author" in description
    assert "- **post** → Relationship: Post being commented on" in description


def test_describe_model_with_complex_types():
    """Test describe_model with complex field types."""
    app = EnrichMCP("Content Management", description="A CMS data model")

    # Define an entity with complex types
    @app.entity(description="Article entity with complex field types")
    class Article(EnrichModel):
        id: int = Field(description="Unique identifier")
        title: str = Field(description="Article title")
        tags: list[str] = Field(description="Article tags")
        metadata: dict[str, Any] = Field(description="Article metadata")
        categories: set[str] = Field(description="Article categories")

        # Relationship
        author: Relationship = Relationship(description="Article author")

    # Get the model description
    description = app.describe_model()

    # Check the description
    assert "## Article" in description
    assert "Article entity with complex field types" in description
    assert "- **id** (int): Unique identifier" in description
    assert "- **title** (str): Article title" in description

    # Complex types may be rendered differently based on implementation
    # So we check for the field name and description rather than exact type representation
    assert "**tags**" in description and "Article tags" in description
    assert "**metadata**" in description and "Article metadata" in description
    assert "**categories**" in description and "Article categories" in description

    assert "- **author** → Relationship: Article author" in description
