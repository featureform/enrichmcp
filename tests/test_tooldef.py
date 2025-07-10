from unittest.mock import patch

import pytest
from pydantic import Field

from enrichmcp import EnrichMCP, EnrichModel, Relationship


@pytest.mark.asyncio
async def test_tool_description_prefixes() -> None:
    app = EnrichMCP("My API", description="desc")

    with patch.object(app.mcp, "tool", wraps=app.mcp.tool) as mock_tool:

        @app.retrieve(description="get stuff")
        async def get_stuff() -> dict:
            return {}

    desc = mock_tool.call_args.kwargs["description"]
    assert desc.startswith("This is a retriever for the My API server")

    with patch.object(app.mcp, "tool", wraps=app.mcp.tool) as mock_tool:

        @app.create(description="create item")
        async def create_item() -> bool:
            return True

    desc = mock_tool.call_args.kwargs["description"]
    assert desc.startswith("This is a creator for the My API server")

    @app.entity
    class Item(EnrichModel):
        """Item."""

        id: int = Field(description="ID")

    @app.entity
    class User(EnrichModel):
        """User."""

        id: int = Field(description="ID")
        items: list[Item] = Relationship(description="items")

    with patch.object(app.mcp, "tool", wraps=app.mcp.tool) as mock_tool:

        @User.items.resolver
        async def get_items(user_id: int) -> list[Item]:
            return []

    desc = mock_tool.call_args.kwargs["description"]
    assert desc.startswith("This is a resolver for the My API server")
