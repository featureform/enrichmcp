# Hello World Example

A minimal EnrichMCP application exposing a single `hello_world` resource that returns a friendly greeting.

```bash
cd hello_world
python app.py
```

The server listens on `http://localhost:8000`.

## Calling the API with `mcp_use`

Use the provided `client.py` script to start the server and invoke the `hello_world` tool programmatically:

```bash
python client.py
```

This creates an `MCPClient` using a small in-memory configuration, calls the `hello_world` tool, prints the response, and then shuts down the session.
