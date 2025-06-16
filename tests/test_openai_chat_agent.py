import sys
from pathlib import Path

import pytest
from mcp_use import MCPClient


@pytest.mark.examples
@pytest.mark.asyncio
async def test_mcp_client_hello_world():
    example_path = Path(__file__).resolve().parents[1] / "examples" / "hello_world" / "app.py"
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
    tools = await session.connector.list_tools()
    assert any(tool.name == "hello_world" for tool in tools)
    result = await session.connector.call_tool("hello_world", {})
    assert "Hello, World!" in result.content[0].text
    await client.close_all_sessions()
