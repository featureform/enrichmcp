"""Simple mcp-use client for the HTTP example."""

from __future__ import annotations

import asyncio

from mcp_use import MCPClient


async def main() -> None:
    client = MCPClient(config={"mcpServers": {"hello": {"url": "http://localhost:8000/mcp"}}})
    session = await client.create_session("hello")
    result = await session.connector.call_tool("hello_http", {})
    print(result.content[0].text)
    await client.close_all_sessions()


if __name__ == "__main__":
    asyncio.run(main())
