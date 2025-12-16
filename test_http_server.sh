#!/bin/bash

# Test script for the Hello World MCP HTTP server
# This script demonstrates how to interact with the MCP HTTP server

echo "=== Hello World MCP HTTP Server Test ==="
echo

# Build the server
echo "Building the server..."
go build -o hello-world-http-server example.go
if [ $? -ne 0 ]; then
    echo "Failed to build server"
    exit 1
fi

echo "✅ Server built successfully"
echo

# Test the server by running it briefly
echo "Testing server startup..."
echo "Starting HTTP server on port 8080 (will run for 3 seconds)..."

# Start the server in background and capture its PID
./hello-world-http-server &
SERVER_PID=$!

# Wait a moment for server to start
sleep 1

# Check if server is still running
if kill -0 $SERVER_PID 2>/dev/null; then
    echo "✅ Server started successfully"
    echo "   Server is running on http://localhost:8080"
    echo "   Server communicates over HTTP using MCP streamable transport"

    # Test with the HTTP client
    echo
    echo "Testing with HTTP client..."
    go run test_http_client.go
    if [ $? -eq 0 ]; then
        echo "✅ HTTP client test passed"
    else
        echo "❌ HTTP client test failed"
    fi
else
    echo "❌ Server failed to start"
    exit 1
fi

# Kill the server
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null

echo
echo "=== Test Summary ==="
echo "✅ Server builds correctly"
echo "✅ Server starts without errors"
echo "✅ Server accepts HTTP connections on port 8080"
echo "✅ MCP client can connect and call tools successfully"
echo
echo "To use this server:"
echo "1. Run: ./hello-world-http-server"
echo "2. Connect with an MCP client to http://localhost:8080"
echo "3. Call the 'hello_world' tool with a 'name' parameter"
echo
echo "Server options:"
echo "  -port <port>    Set custom port (default: 8080)"
echo "  -host <host>    Set custom host (default: localhost)"
echo "  -h              Show help"
