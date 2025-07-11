from unittest.mock import AsyncMock, Mock, patch

import pytest
from mcp.types import CreateMessageResult, SamplingMessage, TextContent

from enrichmcp import EnrichContext


@pytest.mark.asyncio
async def test_ask_llm_converts_and_calls_session():
    result = CreateMessageResult(
        role="assistant",
        content=TextContent(type="text", text="pong"),
        model="gpt",
    )
    session = Mock()
    session.create_message = AsyncMock(return_value=result)
    request_ctx = Mock(session=session)
    ctx = EnrichContext.model_construct(_request_context=request_ctx)

    msg = SamplingMessage(role="assistant", content=TextContent(type="text", text="hi"))
    got = await ctx.ask_llm(["ping", msg], temperature=0.1, allow_tools="thisServer")

    assert got is result
    session.create_message.assert_awaited_once()
    called = session.create_message.call_args.kwargs
    assert called["temperature"] == 0.1
    assert called["include_context"] == "thisServer"
    assert called["messages"][0].role == "user"
    assert called["messages"][0].content.text == "ping"
    assert called["messages"][1] == msg


@pytest.mark.asyncio
async def test_sampling_alias_and_type_error():
    ctx = EnrichContext.model_construct(_request_context=Mock(session=Mock()))

    # Alias should delegate to ask_llm
    with patch.object(EnrichContext, "ask_llm", AsyncMock(return_value="ok")) as mock:
        result = await ctx.sampling("hello")
        assert result == "ok"
        mock.assert_awaited_once()

    # Invalid message type raises TypeError
    with pytest.raises(TypeError):
        await ctx.sampling([123])


@pytest.mark.asyncio
async def test_ask_llm_requires_request_context():
    ctx = EnrichContext()
    with pytest.raises(ValueError, match="outside of a request"):
        await ctx.ask_llm("ping")
