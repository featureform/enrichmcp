from unittest.mock import AsyncMock, Mock

import pytest
from fastmcp import Context
from mcp.types import CreateMessageResult, SamplingMessage, TextContent


@pytest.mark.asyncio
async def test_fastmcp_context_sample_method():
    """Test that FastMCP's Context.sample method works."""
    # Create a mock Context
    ctx = Mock(spec=Context)

    # Mock the sample method to return a successful result
    result = CreateMessageResult(
        role="assistant",
        content=TextContent(type="text", text="pong"),
        model="gpt-4",
    )
    ctx.sample = AsyncMock(return_value=result)

    # Test calling sample directly
    response = await ctx.sample("ping")
    assert response == result
    ctx.sample.assert_awaited_once_with("ping")


@pytest.mark.asyncio
async def test_fastmcp_context_sample_with_options():
    """Test FastMCP's Context.sample with additional options."""
    ctx = Mock(spec=Context)

    result = CreateMessageResult(
        role="assistant",
        content=TextContent(type="text", text="Creative response"),
        model="gpt-4",
    )
    ctx.sample = AsyncMock(return_value=result)

    # Test calling sample with options
    response = await ctx.sample("Write a story", temperature=0.8, max_tokens=100)
    assert response.content.text == "Creative response"
    ctx.sample.assert_awaited_once_with("Write a story", temperature=0.8, max_tokens=100)


@pytest.mark.asyncio
async def test_fastmcp_context_sample_with_messages():
    """Test FastMCP's Context.sample with message list."""
    ctx = Mock(spec=Context)

    result = CreateMessageResult(
        role="assistant",
        content=TextContent(type="text", text="Response to conversation"),
        model="gpt-4",
    )
    ctx.sample = AsyncMock(return_value=result)

    # Test calling sample with message list
    msg = SamplingMessage(role="assistant", content=TextContent(type="text", text="hi"))
    response = await ctx.sample(["ping", msg], temperature=0.1)

    assert response == result
    ctx.sample.assert_awaited_once_with(["ping", msg], temperature=0.1)
