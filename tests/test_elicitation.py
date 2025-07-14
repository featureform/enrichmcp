from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic import BaseModel

from enrichmcp import EnrichContext


class Prefs(BaseModel):
    choice: bool


@pytest.mark.asyncio
async def test_ask_user_delegates_to_context_elicit():
    ctx = EnrichContext.model_construct(_request_context=Mock())

    with patch("enrichmcp.context.Context.elicit", AsyncMock(return_value="ok")) as mock:
        got = await ctx.ask_user("hi", Prefs)
        assert got == "ok"
        mock.assert_awaited_once_with(message="hi", schema=Prefs)


@pytest.mark.asyncio
async def test_ask_user_requires_request_context():
    ctx = EnrichContext()

    with pytest.raises(ValueError, match="outside of a request"):
        await ctx.ask_user("hi", Prefs)
