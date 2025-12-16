# Hello World MCP HTTP Server in Go

This is a simple example of a Model Context Protocol (MCP) server written in Go using the official Go SDK with **HTTP transport**.

## What it does

This server provides a single tool called `hello_world` that:
- Takes a `name` parameter (string)
- Returns a personalized greeting message

## Prerequisites

- Go 1.21 or later
- The MCP Go SDK

## Setup

1. Initialize the Go module and download dependencies:
```bash
go mod tidy
```

2. Build the server:
```bash
go build -o hello-world-http-server example.go
```

## Running the Server

The server communicates over HTTP using streamable transport. You can configure the host and port:

```bash
# Default (localhost:8080)
./hello-world-http-server

# Custom port
./hello-world-http-server -port 9000

# Custom host and port
./hello-world-http-server -host 0.0.0.0 -port 8080

# Show help
./hello-world-http-server -h
```

## Testing with an MCP Client

You can test this server with any MCP client that supports HTTP transport. The server runs on `http://localhost:8080` by default.

Here's an example of how the tool would be called:

**Tool Name:** `hello_world`

**Parameters:**
```json
{
  "name": "World"
}
```

**Expected Response:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Hello, World! Welcome to the MCP Go SDK!"
    }
  ]
}
```

## Code Structure

- `example.go` - Main server implementation
- `go.mod` - Go module definition
- `GO_EXAMPLE.md` - This documentation

## Key Features Demonstrated

1. **Server Creation**: Using `mcp.NewServer()` with basic implementation info
2. **Tool Registration**: Using `mcp.AddTool()` with automatic schema generation
3. **Input Validation**: Using struct tags for JSON schema generation
4. **Content Response**: Returning text content in the MCP format
5. **HTTP Transport**: Using streamable HTTP transport for client communication
6. **Configuration**: Command-line flags for host and port configuration

## Next Steps

To extend this example, you could:
- Add more tools with different functionality
- Implement resource providers
- Add prompt templates
- Use different transport mechanisms (HTTP, WebSocket, etc.)
- Add error handling and logging

For more advanced examples, check out the [official Go SDK repository](https://github.com/modelcontextprotocol/go-sdk).

## Testing the Server

To test that the server works correctly, you can:

1. Build and run the server:
```bash
go build -o hello-world-http-server example.go
./hello-world-http-server
```

2. The server will start and listen for HTTP connections. You'll see output like:
```
2025/12/15 18:01:16 Starting hello world MCP server on http://localhost:8080
2025/12/15 18:01:16 Available tool: hello_world (parameter: name)
```

3. Test with the included test client:
```bash
go run test_http_client.go
```

4. Or use any MCP client that supports HTTP transport by connecting to `http://localhost:8080`.
