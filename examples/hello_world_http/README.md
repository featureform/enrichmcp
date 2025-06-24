# Hello World HTTP Example

A minimal EnrichMCP application served over **streamable HTTP** rather than the default stdio transport.

```bash
cd hello_world_http
python app.py
```

The server listens on `http://localhost:8000/mcp`.

## Calling the API with `mcp_use`

Run the companion `client.py` script to call the `hello_http` tool using the official Python SDK:

```bash
python client.py
```
