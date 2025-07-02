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
async def get_data(context: MyContext) -> dict:
    # Use your custom context
    return await context.db.fetch_data()
```

Note: Full context support with dependency injection is planned for future releases.
