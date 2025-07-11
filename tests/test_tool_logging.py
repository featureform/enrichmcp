from unittest.mock import AsyncMock, patch

import pytest

from enrichmcp import EnrichContext, EnrichMCP


@pytest.mark.asyncio
async def test_wrapper_logging_and_return() -> None:
    app = EnrichMCP("Test", description="desc")

    async def orig(ctx: EnrichContext) -> str:
        return "ok"

    with patch.object(app.mcp, "tool", wraps=app.mcp.tool) as mock_tool:
        wrapped = app.retrieve(description="desc")(orig)

    assert wrapped is not orig
    assert wrapped.__wrapped__ is orig

    ctx = EnrichContext.model_construct(_request_context=AsyncMock())
    with patch.object(EnrichContext, "debug", AsyncMock()) as debug:
        result = await wrapped(ctx)
        assert result == "ok"
        debug.assert_any_call("Calling orig")
        debug.assert_any_call("orig completed")

    # Ensure FastMCP registration called
    assert mock_tool.called
