import os
import sys
from pathlib import Path

import pytest
from mcp import ClientSessionGroup, StdioServerParameters


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

    # Clean up database file if created by shop_api_sqlite example
    if db_path.exists():
        db_path.unlink()
