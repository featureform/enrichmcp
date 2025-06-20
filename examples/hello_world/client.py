"""Example mcp-use client for the Hello World API."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from mcp_use import MCPClient


async def main() -> None:
    example_path = Path(__file__).parent / "app.py"

    config = {
        "mcpServers": {
            "hello": {
                "command": sys.executable,
                "args": [str(example_path)],
            }
        }
    }

    client = MCPClient(config=config)
    session = await client.create_session("hello")
    result = await session.connector.call_tool("hello_world", {})
    print(result.content[0].text)

    await client.close_all_sessions()


if __name__ == "__main__":
    asyncio.run(main())
