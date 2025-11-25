# Context

EnrichMCP uses FastMCP's Context system for request-scoped utilities including logging, progress reporting, and lifespan context access.

## Overview

FastMCP's `Context` provides comprehensive request-scoped functionality:
- **Logging**: Send debug, info, warning, and error messages to clients
- **Progress Reporting**: Update clients on long-running operations
- **Lifespan Context**: Access shared resources like database connections
- **LLM Sampling**: Request completions from client-side LLMs
- **User Elicitation**: Request structured input from users

## Usage Patterns

**Recommended: Dependency Injection**
```python
from fastmcp import Context


@app.retrieve()
async def my_resource(ctx: Context) -> dict:
    # Access lifespan context (database, etc.)
    db = ctx.request_context.lifespan_context["db"]

    # Use built-in logging
    await ctx.info("Processing request")

    return {"result": "success"}
```

**Alternative: Helper Function**
```python
from enrichmcp import get_enrich_context


def helper_function():
    ctx = get_enrich_context()
    db = ctx.request_context.lifespan_context["db"]
```

## Core Capabilities

### Logging
```python
@app.retrieve()
async def my_tool(ctx: Context) -> dict:
    await ctx.debug("Debug message")
    await ctx.info("Info message")
    await ctx.warning("Warning message")
    await ctx.error("Error message")
    return {"status": "logged"}
```

### Progress Reporting
```python
@app.retrieve()
async def long_task(ctx: Context) -> dict:
    await ctx.report_progress(progress=25, total=100)
    # ... do work ...
    await ctx.report_progress(progress=100, total=100)
    return {"status": "complete"}
```

### Lifespan Context Access
```python
@app.retrieve()
async def database_query(ctx: Context) -> list[dict]:
    # Access shared resources from lifespan context
    db = ctx.request_context.lifespan_context["db"]
    cache = ctx.request_context.lifespan_context.get("cache")

    return await db.fetch_all("SELECT * FROM users")
```

## LLM Integration

Use `sample()` to request completions from the client-side LLM:

```python
from enrichmcp import prefer_fast_model


@app.retrieve()
async def analyze_data(ctx: Context) -> dict:
    result = await ctx.sample(
        "Summarize our latest sales numbers",
        model_preferences=prefer_fast_model(),
        max_tokens=200,
    )
    return {"analysis": result.content.text}
```

For more details, see the [FastMCP Context documentation](https://gofastmcp.com/servers/context).
