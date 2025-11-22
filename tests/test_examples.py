import os
import sys
from pathlib import Path

import pytest
from mcp import ClientSessionGroup, StdioServerParameters

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
            # Try to call a simple tool that doesn't need parameters
            simple_tool_names = ["hello_world", "list_users", "list_products", "explore_data_model"]
            simple_tools = [t for t in tools_result.tools if t.name in simple_tool_names]
            if simple_tools:
                tool = simple_tools[0]
                # Only call tools that actually don't require parameters
                if not tool.inputSchema or not tool.inputSchema.get("required"):
                    result = await session.call_tool(tool.name, {})
                    # Basic validation that the tool returned something
                    assert result is not None

    # Clean up database file if created by shop_api_sqlite example
    if db_path.exists():
        db_path.unlink()
