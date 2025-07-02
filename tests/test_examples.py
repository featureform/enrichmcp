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
        await session.list_tools()

    # Clean up database file if created by shop_api_sqlite example
    if db_path.exists():
        db_path.unlink()
