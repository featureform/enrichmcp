# Server-Side LLM Travel Planner

This example demonstrates how an EnrichMCP server can use the `ctx.sampling()`
helper to ask the client for language model assistance.

The API exposes two resources:

- `list_destinations()` – returns a list of predefined destinations
- `plan_trip(preferences)` – uses LLM sampling to pick the top three destinations
  that match the user's preferences

Run the server:

```bash
python app.py
```

Then invoke it with an MCP client such as `mcp_use` or the `openai_chat_agent`
example. Describe your travel preferences and the server will respond with three
suggested destinations.
