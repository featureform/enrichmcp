import pytest
from pydantic import Field

from enrichmcp import DataModelSummary, EnrichMCP, EnrichModel


@pytest.mark.asyncio
async def test_explore_data_model_returns_summary() -> None:
    app = EnrichMCP("My API", description="Demo server")

    @app.entity(description="Test entity")
    class Item(EnrichModel):
        id: int = Field(description="Identifier")

    tool_name = "explore_my_api_data_model"
    assert tool_name in app.resources

    summary = await app.resources[tool_name]()
    assert isinstance(summary, DataModelSummary)
    assert summary.title == "My API"
    assert summary.description == "Demo server"
    assert summary.entity_count == 1
    assert summary.entities == ["Item"]
    assert isinstance(summary.model, str)
    assert "Item" in summary.model

    summary_text = str(summary)
    assert "# My API" in summary_text
    assert "**Entity count:** 1" in summary_text
    assert "- Item" in summary_text

    tools = await app.mcp.list_tools()
    tool = next(t for t in tools if t.name == tool_name)
    assert "start of an agent session" in tool.description
    assert "Demo server" in tool.description
