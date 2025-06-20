# Error Handling

## Overview

The errors module is currently a placeholder for future error handling functionality. enrichmcp currently relies on Python's built-in exceptions and Pydantic's validation errors.

## Current Error Handling

### Pydantic Validation

enrichmcp leverages Pydantic's built-in validation:

```python
from pydantic import ValidationError

try:
    user = User(id="not-a-number", email="invalid")
except ValidationError as e:
    print(e.json())
    # {
    #   "detail": [
    #     {
    #       "loc": ["id"],
    #       "msg": "value is not a valid integer",
    #       "type": "type_error.integer"
    #     }
    #   ]
    # }
```

### Built-in Exceptions

Use Python's standard exceptions:

```python
@app.retrieve
async def get_user(user_id: int) -> User:
    user = find_user(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    return user
```

### Resolver Validation

enrichmcp validates resolver return types at startup:

```python
# This will raise TypeError on app.run()
@User.orders.resolver
async def bad_resolver(user_id: int) -> str:  # Wrong type!
    return "not a list of orders"
```

## Future Error Support

The errors module is designed to eventually provide:

- Semantic error types (NotFoundError, ValidationError, etc.)
- Rich error metadata
- Consistent error responses
- Integration with MCP error handling

For now, use standard Python exceptions and Pydantic validation.
