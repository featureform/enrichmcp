# Test configuration for enrichmcp
import asyncio

import pytest
import pytest_asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_test_environment():
    """Setup test environment for each test."""
    # Add any global test setup here
    yield
    # Add any global test cleanup here
