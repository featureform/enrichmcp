// Test client for the Hello World MCP HTTP server
// This demonstrates how to connect to and interact with the HTTP MCP server
package main

import (
	"context"
	"log"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

func main() {
	ctx := context.Background()

	log.Println("=== MCP HTTP Client Test ===")

	// Create an MCP client
	client := mcp.NewClient(&mcp.Implementation{
		Name:    "test-client",
		Version: "1.0.0",
	}, nil)

	// Connect to the HTTP server
	log.Println("Connecting to MCP server at http://localhost:8080...")
	session, err := client.Connect(ctx, &mcp.StreamableClientTransport{
		Endpoint: "http://localhost:8080",
	}, nil)
	if err != nil {
		log.Fatalf("Failed to connect: %v", err)
	}
	defer session.Close()

	log.Printf("✅ Connected to server (session ID: %s)", session.ID())

	// List available tools
	log.Println("📋 Listing available tools...")
	toolsResult, err := session.ListTools(ctx, nil)
	if err != nil {
		log.Fatalf("Failed to list tools: %v", err)
	}

	for _, tool := range toolsResult.Tools {
		log.Printf("   - %s: %s", tool.Name, tool.Description)
	}

	// Call the hello_world tool with different names
	names := []string{"World", "Alice", "Go Developer"}

	log.Println("🔧 Testing hello_world tool...")
	for _, name := range names {
		log.Printf("   Calling with name: %s", name)
		result, err := session.CallTool(ctx, &mcp.CallToolParams{
			Name: "hello_world",
			Arguments: map[string]any{
				"name": name,
			},
		})
		if err != nil {
			log.Printf("   ❌ Failed to call tool: %v", err)
			continue
		}

		// Print the result
		for _, content := range result.Content {
			if textContent, ok := content.(*mcp.TextContent); ok {
				log.Printf("   ✅ Result: %s", textContent.Text)
			}
		}
	}

	log.Println("🎉 Test completed successfully!")
}
