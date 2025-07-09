from unittest.mock import patch

import pytest

from enrichmcp import EnrichContext, EnrichMCP, EnrichParameter


@pytest.mark.asyncio
async def test_enrichparameter_hints_appended():
    app = EnrichMCP("Test", description="desc")
    with patch.object(app.mcp, "tool", wraps=app.mcp.tool) as mock_tool:

        @app.retrieve(description="Base desc")
        async def my_resource(
            ctx: EnrichContext,
            name: str = EnrichParameter(description="user name", examples=["bob"]),
        ) -> dict:
            return {}

    desc = mock_tool.call_args.kwargs["description"]
    assert "Parameter hints:" in desc
    assert "name - str" in desc
    assert "user name" in desc
    assert "examples: bob" in desc
    assert "ctx" not in desc
