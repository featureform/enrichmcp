"""Utility helpers for combining lifespan context managers."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager
from typing import Any

from .app import EnrichMCP

Lifespan = Callable[[EnrichMCP], AbstractAsyncContextManager[dict[str, Any]]]


def combine_lifespans(*lifespans: Lifespan) -> Lifespan:
    """Combine multiple lifespan functions into one.

    Each lifespan may yield a dict of context values. The returned context will
    merge all of these dictionaries. Later lifespans override keys from earlier
    ones if they conflict.
    """

    @asynccontextmanager
    async def _combined(app: EnrichMCP) -> AsyncIterator[dict[str, Any]]:
        async with AsyncExitStack() as stack:
            merged: dict[str, Any] = {}
            for ls in lifespans:
                ctx: dict[str, Any] = await stack.enter_async_context(ls(app))
                if isinstance(ctx, dict):
                    merged.update(ctx)
            yield merged

    return _combined
