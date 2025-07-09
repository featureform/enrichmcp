# Parameter Metadata

`EnrichParameter` attaches hints like descriptions and examples to function parameters.
When a parameter's default value is an instance of `EnrichParameter`, those hints
are appended to the generated tool description (except for parameters typed as
`EnrichContext`).

```python
from enrichmcp import EnrichParameter

@app.retrieve
async def greet(name: str = EnrichParameter(description="user name", examples=["bob"])) -> str:
    return f"Hello {name}"
```
