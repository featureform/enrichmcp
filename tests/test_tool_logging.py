from unittest.mock import AsyncMock, Mock

import pytest

from enrichmcp import EnrichContext, EnrichMCP


@pytest.mark.asyncio
async def test_tool_logs_call_params():
    app = EnrichMCP("Test", description="d")

    @app.retrieve(description="say hi")
    async def greet(name: str, ctx: EnrichContext) -> str:
        return f"hi {name}"

    mock_ctx = Mock(spec=EnrichContext)
    mock_ctx.info = AsyncMock()

    result = await greet(name="bob", ctx=mock_ctx)

    assert result == "hi bob"
    mock_ctx.info.assert_awaited_once()
    args, kwargs = mock_ctx.info.call_args
    assert "greet" in args[0]
    assert "'name': 'bob'" in args[0]
