import os
import sys
from pathlib import Path

import pytest
from mcp import ClientSessionGroup, StdioServerParameters

# Import Redis fixtures if available
try:
    from tests.redis.conftest import redis_container
except ImportError:
    redis_container = None


def is_parameter_free_tool(tool) -> bool:
    """Check if a tool requires no parameters.

    A tool is considered parameter-free if:
    - It has no inputSchema at all
    - It has an inputSchema but no required fields
    - It has an inputSchema with an empty required list
    """
    if not tool.inputSchema:
        return True

    required = tool.inputSchema.get("required")
    if not required:
        return True

    # Handle edge case: required is an empty list
    return len(required) == 0


EXAMPLES = [
    "hello_world/app.py",
    "shop_api/app.py",
    "shop_api_sqlite/app.py",
    "sqlalchemy_shop/app.py",
    "shop_api_gateway/app.py",
    "basic_memory/app.py",
    "caching/app.py",
    "mutable_crud/app.py",
    "server_side_llm_travel_planner/app.py",
]

# Redis examples require Redis to be running
REDIS_EXAMPLES = [
    "redis_shop/app.py",
]


@pytest.mark.examples
@pytest.mark.asyncio
@pytest.mark.parametrize("example", EXAMPLES)
async def test_example_runs(example):
    example_path = Path(__file__).resolve().parents[1] / "examples" / example
    db_path = example_path.parent / "shop.db"
    if db_path.exists():
        db_path.unlink()

    params = StdioServerParameters(
        command=sys.executable,
        args=[str(example_path)],
        env=os.environ.copy(),
    )
    async with ClientSessionGroup() as group:
        session = await group.connect_to_server(params)
        tools_result = await session.list_tools()

        # Test that tools actually work by calling one
        if tools_result.tools:
            # Find any tool that doesn't need parameters
            parameter_free_tools = [t for t in tools_result.tools if is_parameter_free_tool(t)]

            if parameter_free_tools:
                # Try the first parameter-free tool we find
                tool = parameter_free_tools[0]
                try:
                    result = await session.call_tool(tool.name, {})
                    # Basic validation that the tool returned something
                    assert result is not None
                except Exception as e:
                    pytest.fail(f"Failed to call parameter-free tool '{tool.name}': {e}")
            # If no parameter-free tools exist, that's okay - just verify server starts


@pytest.mark.examples
@pytest.mark.asyncio
@pytest.mark.parametrize("example", REDIS_EXAMPLES)
async def test_redis_example_runs(example, redis_container):
    """Test Redis examples with Redis container."""
    if redis_container is None:
        pytest.skip("Redis container fixture not available")

    example_path = Path(__file__).resolve().parents[1] / "examples" / example
    db_path = example_path.parent / "shop.db"

    # Set Redis URL for the test
    redis_url = f"redis://{redis_container['host']}:{redis_container['port']}"
    test_env = dict(os.environ)
    test_env["REDIS_URL"] = redis_url

    try:
        params = StdioServerParameters(
            command=sys.executable, args=[str(example_path)], env=test_env
        )

        async with ClientSessionGroup() as group:
            session = await group.connect_to_server(params)

            # Test basic functionality
            tools_result = await session.list_tools()
            assert tools_result.tools is not None
            assert len(tools_result.tools) > 0

            tool_names = [tool.name for tool in tools_result.tools]

            # Verify Redis-specific tools exist
            expected_redis_tools = [
                "search_user_by_text",
                "filter_user_by_account_status",
                "get_user_by_id",
                # Note: get_user_orders removed due to reverse relationship removal
            ]

            for tool_name in expected_redis_tools:
                assert (
                    tool_name in tool_names
                ), f"Expected Redis tool '{tool_name}' not found in {tool_names}"

            # Test a simple tool call that should work
            try:
                result = await session.call_tool("get_user_by_id", {"id": 1})
                assert result is not None
                assert result.content[0].text is not None
                print(f"✅ Redis shop tool call successful: {result.content[0].text[:100]}...")
            except Exception as e:
                pytest.fail(f"Failed to call get_user_by_id tool: {e}")

    except Exception as e:
        pytest.fail(f"Redis example failed to run: {e}")

    # Clean up database file if created by shop_api_sqlite example
    if db_path.exists():
        db_path.unlink()
