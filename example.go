// Copyright 2025 The Go MCP SDK Authors. All rights reserved.
// Use of this source code is governed by an MIT-style
// license that can be found in the LICENSE file.

// Simple hello world MCP server with a single tool.
// This server demonstrates the basic usage of the Go MCP SDK.
//
// It runs over HTTP using streamable transport and provides a single "hello_world" tool
// that returns a greeting message.
package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

var (
	host = flag.String("host", "localhost", "host to listen on")
	port = flag.Int("port", 8080, "port number to listen on")
)

func main() {
	out := flag.CommandLine.Output()
	flag.Usage = func() {
		fmt.Fprintf(out, "Usage: %s [-port <port>] [-host <host>]\n\n", os.Args[0])
		fmt.Fprintf(out, "This program demonstrates MCP over HTTP using the streamable transport.\n")
		fmt.Fprintf(out, "It provides a single 'hello_world' tool that greets a person by name.\n\n")
		fmt.Fprintf(out, "Options:\n")
		flag.PrintDefaults()
		fmt.Fprintf(out, "\nExamples:\n")
		fmt.Fprintf(out, "  Default:        %s\n", os.Args[0])
		fmt.Fprintf(out, "  Custom port:    %s -port 9000\n", os.Args[0])
		fmt.Fprintf(out, "  Custom host:    %s -host 0.0.0.0 -port 8080\n", os.Args[0])
		os.Exit(1)
	}
	flag.Parse()
	// Create a server with basic implementation info
	server := mcp.NewServer(&mcp.Implementation{
		Name:    "hello-world-server",
		Version: "1.0.0",
	}, nil)

	// Define the input structure for our hello world tool
	type HelloWorldArgs struct {
		Name string `json:"name" jsonschema:"the name of the person to greet"`
	}

	// Add the hello world tool to the server
	// The AddTool function automatically generates the JSON schema
	// from the struct tags for input validation
	mcp.AddTool(server, &mcp.Tool{
		Name:        "hello_world",
		Description: "A simple tool that greets a person by name",
	}, func(ctx context.Context, req *mcp.CallToolRequest, args HelloWorldArgs) (*mcp.CallToolResult, any, error) {
		// Create the greeting message
		greeting := "Hello, " + args.Name + "! Welcome to the MCP Go SDK!"

		// Return the result with text content
		return &mcp.CallToolResult{
			Content: []mcp.Content{
				&mcp.TextContent{Text: greeting},
			},
		}, nil, nil
	})

	// Create the streamable HTTP handler
	handler := mcp.NewStreamableHTTPHandler(func(req *http.Request) *mcp.Server {
		return server
	}, nil)

	url := fmt.Sprintf("%s:%d", *host, *port)
	log.Printf("Starting hello world MCP server on http://%s", url)
	log.Printf("Available tool: hello_world (parameter: name)")

	// Start the HTTP server
	if err := http.ListenAndServe(url, handler); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
