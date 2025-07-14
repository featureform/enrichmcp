# Server-Side LLM Sampling

MCP includes a **sampling** feature that lets the server ask the client to run an LLM request.
This keeps API keys and billing on the client side while giving your EnrichMCP
application the ability to generate text or run tool-aware prompts.

`EnrichContext.ask_llm()` (and its alias `sampling()`) is the helper used to make
these requests. The method mirrors the MCP sampling API and supports a number of
tuning parameters.

## Parameters

| Name | Description |
|------|-------------|
| `messages` | Text or `SamplingMessage` objects to send to the LLM. Strings are converted to user messages automatically. |
| `system_prompt` | Optional system prompt that defines overall behavior. |
| `max_tokens` | Maximum number of tokens the client should generate. Defaults to 1000. |
| `temperature` | Sampling temperature for controlling randomness. |
| `model_preferences` | `ModelPreferences` object describing cost, speed and intelligence priorities. Use `prefer_fast_model()`, `prefer_medium_model()` or `prefer_smart_model()` as shortcuts. |
| `allow_tools` | Controls what tools the LLM can see: `"none"`, `"thisServer"`, or `"allServers"`. |
| `stop_sequences` | Strings that stop generation when encountered. |

### Model Preferences

`ModelPreferences` let the server express whether it cares more about cost,
speed or intelligence when the client chooses an LLM. Two convenience functions
are provided:

```python
from enrichmcp import prefer_fast_model, prefer_medium_model, prefer_smart_model
```

Use `prefer_fast_model()` when low latency and price are most important.
`prefer_medium_model()` offers balanced quality and cost. Use `prefer_smart_model()` when you need the best reasoning capability.

### Tool Access

Set `allow_tools` to allow the client LLM to inspect available MCP tools.
This enables context-aware answers where the LLM can suggest reading or calling
other resources.

## Example

```python
@app.retrieve
async def summarize(text: str) -> str:
    ctx = app.get_context()
    result = await ctx.ask_llm(
        f"Summarize this: {text}",
        model_preferences=prefer_fast_model(),
        max_tokens=200,
        allow_tools="thisServer",
    )
    return result.content.text
```

MCP sampling gives your server lightweight LLM features without storing API
credentials. See the [travel planner example](../examples/server_side_llm_travel_planner) for a complete
implementation.
