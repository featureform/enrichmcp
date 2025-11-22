from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastmcp import Context


@pytest.mark.asyncio
async def test_elicit_with_string_response():
    """Test FastMCP's Context.elicit with string response type."""
    # Create a mock Context with elicit method
    ctx = Mock(spec=Context)

    # Mock the elicit method to return a successful result
    mock_result = SimpleNamespace(action="accept", data="John Doe")
    ctx.elicit = AsyncMock(return_value=mock_result)

    # Test calling elicit directly
    result = await ctx.elicit("What's your name?", response_type=str)
    assert result.action == "accept"
    assert result.data == "John Doe"
    ctx.elicit.assert_awaited_once_with("What's your name?", response_type=str)


@pytest.mark.asyncio
async def test_elicit_with_decline_action():
    """Test FastMCP's Context.elicit when user declines."""
    ctx = Mock(spec=Context)

    # Mock the elicit method to return a decline result
    mock_result = SimpleNamespace(action="decline", data=None)
    ctx.elicit = AsyncMock(return_value=mock_result)

    # Test calling elicit directly
    result = await ctx.elicit("Enter your age:", response_type=int)
    assert result.action == "decline"
    assert result.data is None
    ctx.elicit.assert_awaited_once_with("Enter your age:", response_type=int)


@pytest.mark.asyncio
async def test_elicit_with_cancel_action():
    """Test FastMCP's Context.elicit when user cancels."""
    ctx = Mock(spec=Context)

    # Mock the elicit method to return a cancel result
    mock_result = SimpleNamespace(action="cancel", data=None)
    ctx.elicit = AsyncMock(return_value=mock_result)

    # Test calling elicit directly
    result = await ctx.elicit("Continue?", response_type=None)
    assert result.action == "cancel"
    assert result.data is None
    ctx.elicit.assert_awaited_once_with("Continue?", response_type=None)
