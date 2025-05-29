# Context

::: enrichmcp.context.EnrichContext
    options:
        show_source: true
        show_bases: true
        show_root_heading: true

## Overview

The `EnrichContext` class provides a placeholder for future context functionality. Currently, it's a minimal implementation that can be extended for request-scoped dependencies.

## Current State

```python
from enrichmcp import EnrichContext

# Current implementation is minimal
context = EnrichContext()
```

## Future Use Cases

The context system is designed to eventually support:

- Database connections
- Authentication information
- Request metadata
- Dependency injection

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
@app.resource
async def get_data(context: MyContext) -> dict:
    # Use your custom context
    return await context.db.fetch_data()
```

Note: Full context support with dependency injection is planned for future releases.
