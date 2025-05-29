import asyncio
import contextlib
from collections.abc import AsyncIterator
from typing import Any

import pytest

from enrichmcp import EnrichContext

# Register pytest-asyncio plugin
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    # Use new_event_loop instead of get_event_loop_policy().new_event_loop()
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@contextlib.asynccontextmanager
async def create_test_context(
    *, db: Any | None = None, user_id: int | None = None, scopes: set[str] | None = None
) -> AsyncIterator[EnrichContext]:
    """
    Create a test context for unit testing resources.

    Args:
        db: Database connection or mock
        user_id: Optional user ID for authentication
        scopes: Optional permission scopes

    Yields:
        Context object for testing
    """
    yield EnrichContext()
