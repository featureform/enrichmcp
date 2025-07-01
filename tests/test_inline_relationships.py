import pytest
from pydantic import Field

from enrichmcp import EnrichMCP, EnrichModel, Relationship, inline_relationships


@pytest.mark.asyncio
async def test_inline_simple_relationship():
    app = EnrichMCP("Test", description="Inline test")

    @app.entity
    class Item(EnrichModel):
        """Item entity"""

        id: int = Field(description="ID")

    @app.entity
    class User(EnrichModel):
        """User entity"""

        id: int = Field(description="ID")
        items: list[Item] = Relationship(description="items", inline=True)

    @User.items.resolver
    async def get_items(user_id: int) -> list[Item]:
        return [Item(id=1), Item(id=2)]

    @app.retrieve(description="Get user")
    async def get_user(user_id: int) -> User:
        return User(id=user_id)

    result = await get_user(user_id=123)
    assert len(result.items) == 2
    assert isinstance(result.items[0], Item)


@pytest.mark.asyncio
async def test_inline_relationship_depth():
    app = EnrichMCP("Test", description="Depth test")

    @app.entity
    class Child(EnrichModel):
        """Child entity"""

        id: int = Field(description="ID")
        parent: "Parent" = Relationship(description="parent", inline=True)

    @app.entity
    class Parent(EnrichModel):
        """Parent entity"""

        id: int = Field(description="ID")
        child: Child = Relationship(description="child", inline=True)

    # Rebuild models for forward references
    Child.model_rebuild(_types_namespace={"Parent": Parent, "Child": Child})
    Parent.model_rebuild(_types_namespace={"Parent": Parent, "Child": Child})

    @Parent.child.resolver
    async def get_child(parent_id: int) -> Child:
        return Child(id=parent_id)

    @Child.parent.resolver
    async def get_parent(child_id: int) -> Parent:
        return Parent(id=child_id)

    parent = Parent(id=1)
    result = await inline_relationships(parent, max_depth=2, only_inline=True)
    assert isinstance(result.child, Child)
    assert isinstance(result.child.parent, Parent)
    # Depth limit prevents full cycle
    assert getattr(result.child.parent, "child", None) is None
