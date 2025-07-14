# Context

::: enrichmcp.context.EnrichContext
    options:
        show_source: true
        show_bases: true
        show_root_heading: true

## Overview

The `EnrichContext` class provides request-scoped utilities such as the cache system.
It can be extended for additional dependencies as needed.

## Current State

```python
from enrichmcp import EnrichContext

# Current implementation is minimal
context = EnrichContext()
```

## Capabilities

The context exposes a `cache` attribute for storing values across the request,
user, or global scopes.

## LLM Integration

Use `ask_llm()` (or the `sampling()` alias) to request completions from the client-side LLM. See the [Server-Side LLM guide](../server_side_llm.md) for more details:

```python
from enrichmcp import prefer_fast_model, prefer_medium_model, prefer_smart_model

result = await ctx.ask_llm(
    "Summarize our latest sales numbers",
    model_preferences=prefer_fast_model(),
    max_tokens=200,
)
print(result.content.text)
```

## User Elicitation

Call `ask_user()` when you need additional input from the client. It wraps the
underlying MCP `elicit()` API:

```python
class BookingPreferences(BaseModel):
    alternativeDate: str | None
    checkAlternative: bool = False

result = await ctx.ask_user(
    message="No tables available. Try another date?",
    schema=BookingPreferences,
)
```

## Extending Context

For now, if you need context functionality, you can extend the base class:

```python
from enrichmcp import EnrichContext


class MyContext(EnrichContext):
    """Custom context with database."""

    def __init__(self, db):
        super().__init__()
        self.db = db


# Use in resources
@app.retrieve
async def get_data() -> dict:
    ctx = app.get_context()
    # Use your custom context
    return await ctx.db.fetch_data()
```

Note: Dependency injection is no longer supported; always call ``app.get_context()`` to access the current request context.
