#!/bin/bash

# Simple test script for the hello-world MCP server
# This demonstrates how the server responds to MCP protocol messages

echo "Testing Hello World MCP Server"
echo "==============================="

# Build the server if it doesn't exist
if [ ! -f "hello-world-server" ]; then
    echo "Building server..."
    go build -o hello-world-server example.go
fi

echo ""
echo "Server binary created successfully!"
echo "File size: $(ls -lh hello-world-server | awk '{print $5}')"
echo ""

echo "To test the server manually, you can:"
echo "1. Run: ./hello-world-server"
echo "2. The server will start and wait for MCP JSON-RPC messages on stdin"
echo "3. It implements the 'hello_world' tool that takes a 'name' parameter"
echo ""

echo "Example MCP tool call (JSON-RPC format):"
echo '{'
echo '  "jsonrpc": "2.0",'
echo '  "id": 1,'
echo '  "method": "tools/call",'
echo '  "params": {'
echo '    "name": "hello_world",'
echo '    "arguments": {'
echo '      "name": "World"'
echo '    }'
echo '  }'
echo '}'
echo ""

echo "Expected response would contain:"
echo '"Hello, World! Welcome to the MCP Go SDK!"'
echo ""

echo "Note: For proper testing, use an MCP client or testing framework."
echo "The server communicates using the Model Context Protocol over stdin/stdout."
