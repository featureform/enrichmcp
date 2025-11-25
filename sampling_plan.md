# Sampling Implementation Plan for EnrichMCP

## Current State Analysis

### What Works
- **Real sampling functionality** - `ctx.sample()` is a real FastMCP 2.0 method that works
- **Working examples** - The travel planner example successfully uses sampling
- **Proper documentation** - Most docs show correct `ctx.sample()` usage
- **Integration with EnrichMCP** - Sampling works within EnrichMCP tools via dependency injection

### What's Broken
- **Fake tests in `tests/test_llm.py`** - Meaningless mocked tests that don't test real functionality
- **`ask_llm` mystery** - Used in examples and docs but not defined in EnrichMCP source
- **Mixed documentation** - Some places show `ctx.ask_llm()`, others show `ctx.sample()`
- **No real tests** - Current tests are just mocks that provide false confidence

### Context System Reality
- **FastMCP Context works** - `ctx.sample()` is available via dependency injection
- **EnrichMCP integration works** - Sampling works in `@app.tool()` and `@app.retrieve()` methods
- **Model preferences work** - `prefer_fast_model()`, `prefer_medium_model()`, `prefer_smart_model()` are properly implemented

## FastMCP 2.0 Sampling Requirements

### Core Sampling API
```python
from fastmcp import Context
from enrichmcp import prefer_fast_model

@app.tool()
async def my_tool(ctx: Context) -> str:
    result = await ctx.sample(
        "Summarize this data",
        model_preferences=prefer_fast_model(),
        max_tokens=200,
        temperature=0.7
    )
    return result.content.text
```

### Sampling Result Structure
```python
# CreateMessageResult object has:
result.role         # "assistant"
result.content      # TextContent object
result.content.text # The actual generated text
result.model        # Model name used by client
```

### Supported Parameters
- **`messages`**: String or list of SamplingMessage objects
- **`model_preferences`**: ModelPreferences for client model selection
- **`max_tokens`**: Maximum tokens to generate
- **`temperature`**: Sampling temperature (0.0-2.0)
- **`stop_sequences`**: List of strings that stop generation
- **`allow_tools`**: Tool access level ("none", "thisServer", "allServers")

## Implementation Issues to Resolve

### 1. `ask_llm` Method Mystery
The documentation and examples use `ctx.ask_llm()` but this method doesn't exist in EnrichMCP source:

**Problem locations:**
- `docs/server_side_llm.md` line 48: `await ctx.ask_llm(...)`
- `examples/server_side_llm_travel_planner/app.py` line 75: `await ctx.ask_llm(...)`
- `README.md` line 442: mentions `ctx.ask_llm()` and `ctx.sampling()` alias

**Possible solutions:**
1. **Add `ask_llm` as alias** - Create `ask_llm = sample` in EnrichMCP context
2. **Fix documentation** - Replace all `ask_llm` with `sample`
3. **Investigate FastMCP** - Check if `ask_llm` exists in FastMCP but not documented

### 2. Inconsistent Documentation
- Some docs show `ctx.sample()` (correct)
- Some docs show `ctx.ask_llm()` (undefined)
- Some docs mention `ctx.sampling()` alias (undefined)

## Testing Strategy

### 1. Remove Fake Tests
**Delete entirely**: `tests/test_llm.py` - provides no value, just mocks

### 2. Integration Tests with Real MCP Client
```python
import pytest
from mcp import ClientSession
from fastmcp import FastMCP, Context

@pytest.mark.asyncio
async def test_real_sampling():
    """Test sampling with actual MCP client that supports it."""
    # This requires setting up a real MCP client with sampling support
    # and providing a real LLM backend for testing
    pass
```

### 3. Protocol-Level Tests
```python
@pytest.mark.asyncio
async def test_sampling_protocol():
    """Test that correct MCP sampling messages are sent."""
    # Mock the underlying MCP transport to verify correct protocol messages
    with patch('fastmcp.transport') as mock_transport:
        # Configure mock to return sampling response
        mock_transport.send_request.return_value = CreateMessageResult(
            role="assistant",
            content=TextContent(type="text", text="Generated response"),
            model="gpt-4"
        )

        # Test that tool calls ctx.sample() correctly
        # Verify correct MCP messages are sent
```

### 4. Business Logic Tests
```python
def test_sampling_result_handling():
    """Test how tools handle different sampling results."""
    from mcp.types import CreateMessageResult, TextContent

    def handle_result(result: CreateMessageResult) -> str:
        return f"Model {result.model} said: {result.content.text}"

    result = CreateMessageResult(
        role="assistant",
        content=TextContent(type="text", text="Hello world"),
        model="gpt-4"
    )

    assert handle_result(result) == "Model gpt-4 said: Hello world"
```

## API Design

### 1. Resolve `ask_llm` vs `sample`
**Option A: Add alias in EnrichMCP**
```python
# In src/enrichmcp/context.py or similar
class EnrichContext(Context):
    async def ask_llm(self, *args, **kwargs):
        """Alias for sample() method."""
        return await self.sample(*args, **kwargs)
```

**Option B: Fix all documentation**
```python
# Replace all instances of ctx.ask_llm() with ctx.sample()
# Update examples and documentation
```

**Recommendation: Option B** - Use FastMCP's standard `sample()` method consistently

### 2. Model Preferences Integration
The model preference functions are correctly implemented and should be promoted:
```python
from enrichmcp import prefer_fast_model, prefer_medium_model, prefer_smart_model

@app.tool()
async def smart_analysis(ctx: Context) -> str:
    result = await ctx.sample(
        "Analyze this complex data",
        model_preferences=prefer_smart_model(),  # Use best reasoning model
        max_tokens=500
    )
    return result.content.text
```

## Client Requirements

### 1. MCP Client Support
- Client must implement MCP sampling protocol
- Client must have access to LLM (OpenAI, Anthropic, local models, etc.)
- Client must handle model preferences and parameter tuning

### 2. Model Selection
- Client chooses actual model based on `model_preferences`
- Client handles API keys and billing
- Client respects `max_tokens`, `temperature`, and other parameters

### 3. Error Scenarios
- Client doesn't support sampling → `NotImplementedError`
- LLM API errors → appropriate exceptions
- Network/protocol errors → MCP error responses

## Examples and Use Cases

### 1. Text Generation
```python
@app.tool()
async def generate_summary(text: str, ctx: Context) -> str:
    """Generate a summary of the provided text."""
    result = await ctx.sample(
        f"Summarize this text in 2-3 sentences: {text}",
        model_preferences=prefer_fast_model(),
        max_tokens=100
    )
    return result.content.text
```

### 2. Data Analysis
```python
@app.tool()
async def analyze_trends(data: list[dict], ctx: Context) -> str:
    """Analyze trends in the provided data."""
    data_str = json.dumps(data, indent=2)
    result = await ctx.sample(
        f"Analyze trends in this data and provide insights: {data_str}",
        model_preferences=prefer_smart_model(),
        max_tokens=300,
        temperature=0.3  # Lower temperature for analytical tasks
    )
    return result.content.text
```

### 3. Tool-Aware Generation
```python
@app.tool()
async def smart_assistant(query: str, ctx: Context) -> str:
    """AI assistant that can suggest using other tools."""
    result = await ctx.sample(
        f"Help the user with this query. You can suggest using available tools: {query}",
        model_preferences=prefer_medium_model(),
        allow_tools="thisServer",  # LLM can see available tools
        max_tokens=200
    )
    return result.content.text
```

## Migration Path

### 1. Phase 1: Cleanup (This PR)
- Delete `tests/test_llm.py` - Remove fake tests
- Investigate `ask_llm` vs `sample` discrepancy
- Update TODO item about sampling
- Create this implementation plan

### 2. Phase 2: Fix Documentation (Future PR)
- Replace all `ctx.ask_llm()` with `ctx.sample()` in documentation
- Update examples to use consistent API
- Add real integration tests
- Clarify model preferences usage

### 3. Phase 3: Enhanced Features (Future)
- Advanced sampling patterns and helpers
- Better error handling and fallbacks
- Streaming support if available in FastMCP
- Performance optimizations

## Files to Modify

### Immediate Cleanup (This PR)
1. **DELETE**: `tests/test_llm.py` - Remove fake tests
2. **INVESTIGATE**: `ask_llm` vs `sample` discrepancy in examples
3. **MODIFY**: `TODO` - Update line 4 about sampling
4. **CREATE**: `sampling_plan.md` - This comprehensive plan

### Future Implementation (Separate PR)
1. **MODIFY**: `docs/server_side_llm.md` - Fix `ask_llm` → `sample`
2. **MODIFY**: `examples/server_side_llm_travel_planner/app.py` - Fix `ask_llm` → `sample`
3. **MODIFY**: `README.md` - Fix sampling documentation
4. **CREATE**: `tests/test_sampling_integration.py` - Real tests
5. **OPTIONAL**: Add `ask_llm` alias if needed for backward compatibility

## Key Differences from Elicitation

1. **Sampling Actually Works** - Unlike elicitation, sampling is a real, working feature
2. **Examples Work** - The travel planner example successfully uses sampling
3. **Documentation Mostly Correct** - Just needs `ask_llm` → `sample` fixes
4. **Integration Complete** - Sampling works properly within EnrichMCP's tool system
5. **Only Testing Issue** - The main problem is fake tests, not missing functionality

This plan acknowledges that sampling is a working feature that just needs cleanup of fake tests and documentation consistency, unlike elicitation which needs full implementation.
