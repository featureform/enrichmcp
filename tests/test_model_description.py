from typing import Any, Literal

from pydantic import Field

from enrichmcp import (
    EnrichMCP,
    EnrichModel,
    ModelDescription,
    Relationship,
)


def test_describe_model_empty():
    """Test describe_model with no entities."""
    app = EnrichMCP("Test API", description="Test API description")

    # Get the structured model description
    model = app.describe_model_struct()

    assert model == ModelDescription(
        title="Test API",
        description="Test API description",
        entities=[],
    )


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

    # Get the structured model description
    model = app.describe_model_struct()

    assert model.title == "Social Network"
    assert model.description == "A social network data model"
    assert [e.name for e in model.entities] == ["Comment", "Post", "User"]

    user = next(e for e in model.entities if e.name == "User")
    assert user.description == "User entity for the social network"
    assert [f.name for f in user.fields] == ["id", "name", "email", "is_active"]
    assert {r.name for r in user.relationships} == {"posts", "followers"}

    post = next(e for e in model.entities if e.name == "Post")
    assert post.description == "Post entity for the social network"
    assert [f.name for f in post.fields] == ["id", "title", "content", "published"]
    assert {r.name for r in post.relationships} == {"author", "comments"}

    comment = next(e for e in model.entities if e.name == "Comment")
    assert comment.description == "Comment entity for the social network"
    assert [f.name for f in comment.fields] == ["id", "content"]
    assert {r.name for r in comment.relationships} == {"author", "post"}


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

    # Get the structured model description
    model = app.describe_model_struct()

    assert [e.name for e in model.entities] == ["Article"]

    article = model.entities[0]
    assert article.description == "Article entity with complex field types"
    assert [f.name for f in article.fields] == [
        "id",
        "title",
        "tags",
        "metadata",
        "categories",
    ]
    assert [f.type for f in article.fields] == [
        "int",
        "str",
        "list",
        "dict",
        "set",
    ]
    assert {r.name for r in article.relationships} == {"author"}


def test_describe_model_with_literal_type():
    """Test describe_model with Literal field types."""
    app = EnrichMCP("Enum API", description="A model with Literal fields")

    @app.entity(description="Entity using Literal")
    class Item(EnrichModel):
        status: Literal["pending", "complete"] = Field(description="Item status")

    model = app.describe_model_struct()

    item = model.entities[0]
    assert item.name == "Item"
    assert [f.type for f in item.fields] == ["Literal['pending', 'complete']"]
