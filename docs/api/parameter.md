# Parameter Metadata

`EnrichParameter` attaches hints like descriptions and examples to function parameters.
When a parameter's default value is an instance of `EnrichParameter`, those hints
are appended to the generated tool description (except for parameters typed as
`EnrichContext`). The `default` attribute will also be used as the runtime default
value when the parameter is omitted.

```python
from enrichmcp import EnrichParameter


@app.retrieve
async def greet(
    name: str = EnrichParameter(default="bob", description="user name", examples=["bob"]),
) -> str:
    return f"Hello {name}"


# Omitting ``name`` will now default to "bob"
```
