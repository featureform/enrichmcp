# Hello World MCP HTTP Server

A simple "Hello World" implementation of a Model Context Protocol (MCP) server using the Go SDK with **HTTP transport**.

## What it does

This server provides a single tool called `hello_world` that:
- Takes a `name` parameter (string)
- Returns a personalized greeting message
- Runs over HTTP using streamable transport

## Files

- `example.go` - Main server implementation
- `go.mod` - Go module with MCP SDK dependency
- `GO_EXAMPLE.md` - Detailed documentation
- `test_http_server.sh` - Test script for HTTP server
- `test_http_client.go` - Test client for HTTP server
- `hello-world-http-server` - Compiled binary

## Quick Start

1. Build: `go build -o hello-world-http-server example.go`
2. Run: `./hello-world-http-server` (starts on http://localhost:8080)
3. Connect with an MCP client to `http://localhost:8080` and call the `hello_world` tool

## Configuration

- `-port <port>` - Set custom port (default: 8080)
- `-host <host>` - Set custom host (default: localhost)
- `-h` - Show help

## Testing

Run the test script to verify everything works:
```bash
./test_http_server.sh
```

Or test manually with the included client:
```bash
# Terminal 1: Start server
./hello-world-http-server

# Terminal 2: Test with client
go run test_http_client.go
```

## Example Usage

```bash
# Default port 8080
./hello-world-http-server

# Custom port
./hello-world-http-server -port 9000

# Custom host and port
./hello-world-http-server -host 0.0.0.0 -port 8080
```

The server communicates over HTTP using the MCP streamable transport protocol.

## Key Features

- **HTTP Transport**: Uses streamable HTTP transport instead of stdin/stdout
- **Configurable**: Command-line flags for host and port
- **Type Safe**: Automatic JSON schema generation from Go structs
- **MCP Compliant**: Full MCP protocol implementation
- **Easy Testing**: Includes test client and automated test script

## MCP Tool Details

**Tool Name:** `hello_world`

**Parameters:**
- `name` (string): The name of the person to greet

**Response:**
- Text content with personalized greeting

**Example:**
```json
{
  "name": "hello_world",
  "arguments": {
    "name": "World"
  }
}
```

**Response:**
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
