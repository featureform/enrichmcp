# Elicitation Implementation Plan for EnrichMCP

## Current State Analysis

### What Exists
- **Fake tests in `tests/test_elicitation.py`** - Meaningless mocked tests that don't test real functionality
- **Documentation references** in `docs/api/context.md` (lines 94-119) describing elicitation
- **TODO item** (line 3) mentioning checking elicitation
- **No actual implementation** - No real elicitation functionality in the codebase

### What's Missing
- **Real elicitation implementation** - No `ctx.elicit()` method exists
- **Integration with FastMCP 2.0** - Current approach doesn't align with FastMCP's elicitation system
- **Proper context handling** - EnrichMCP context is broken/deprecated
- **Real tests** - Current tests are just mocks that provide false confidence

### Context System Reality
- **EnrichContext is just an alias** - `EnrichContext = Context` (line 28 in `src/enrichmcp/context.py`)
- **`app.get_context()` is deprecated** - Method exists but has deprecation warnings
- **FastMCP Context is the standard** - All examples use `ctx: Context` dependency injection
- **Mixed documentation** - Some docs show old `app.get_context()`, others show proper dependency injection

## FastMCP 2.0 Elicitation Requirements

### Core Elicitation API
```python
from fastmcp import Context

@app.tool()
async def my_tool(ctx: Context) -> str:
    result = await ctx.elicit(
        message="Please provide your information",
        response_type=str  # or structured types
    )

    if result.action == "accept":
        return f"Got: {result.data}"
    elif result.action == "decline":
        return "Information not provided"
    else:  # cancel
        return "Operation cancelled"
```

### ElicitationResult Structure
```python
# Result object has:
result.action  # "accept", "decline", or "cancel"
result.data    # The actual data (only present when action="accept")
```

### Supported Response Types
- **Scalar types**: `str`, `int`, `bool`, `float`
- **Constrained options**: `["low", "medium", "high"]` or `Literal["yes", "no"]`
- **Structured data**: Dataclasses, TypedDict, Pydantic models
- **No response**: `None` for approval/rejection workflows

## Implementation Architecture

### 1. Context Integration Strategy
Since EnrichMCP context is deprecated, elicitation should work directly with FastMCP's Context:

```python
from fastmcp import Context
from enrichmcp import EnrichMCP

app = EnrichMCP("My API", "Description")

@app.tool()
async def collect_user_data(ctx: Context) -> dict:
    """Collect user information through elicitation."""
    # Use FastMCP's context directly - no EnrichMCP wrapper needed
    result = await ctx.elicit("Enter your name:", response_type=str)

    if result.action == "accept":
        return {"name": result.data, "status": "collected"}
    return {"status": "not_provided", "reason": result.action}
```

### 2. EnrichMCP Integration Points

#### A. Tool Registration
Elicitation should work seamlessly with EnrichMCP's tool system:
```python
@app.tool()  # Uses EnrichMCP's tool decorator
async def interactive_tool(ctx: Context) -> SomeModel:
    # Elicitation works within EnrichMCP tools
    pass
```

#### B. Entity Integration
Elicitation should support EnrichMCP entities as response types:
```python
@app.entity()
class UserProfile(EnrichModel):
    name: str = Field(description="User's full name")
    email: str = Field(description="Email address")

@app.tool()
async def collect_profile(ctx: Context) -> UserProfile:
    result = await ctx.elicit(
        "Please provide your profile information:",
        response_type=UserProfile
    )
    return result.data if result.action == "accept" else None
```

#### C. Relationship Context
Elicitation in relationship resolvers:
```python
@User.orders.resolver
async def get_user_orders(user: User, ctx: Context) -> list[Order]:
    # Could use elicitation for filtering, date ranges, etc.
    filter_result = await ctx.elicit(
        "Filter orders by status?",
        response_type=Literal["all", "pending", "completed"]
    )
    # Apply filtering based on user choice
```

### 3. Error Handling Strategy
```python
async def safe_elicit(ctx: Context, message: str, response_type: type) -> Any:
    """Wrapper for elicitation with proper error handling."""
    try:
        result = await ctx.elicit(message, response_type=response_type)
        return result
    except NotImplementedError:
        # Client doesn't support elicitation
        raise RuntimeError("Client does not support elicitation")
    except Exception as e:
        # Other elicitation errors
        raise RuntimeError(f"Elicitation failed: {e}")
```

## Testing Strategy

### 1. Remove Fake Tests
**Delete entirely**: `tests/test_elicitation.py` - provides no value

### 2. Integration Tests with Real MCP Client
```python
import pytest
from mcp import ClientSession
from fastmcp import FastMCP, Context

@pytest.mark.asyncio
async def test_real_elicitation():
    """Test elicitation with actual MCP client that supports it."""
    # This requires setting up a real MCP client with elicitation support
    # and mocking the user responses at the protocol level
    pass
```

### 3. Protocol-Level Tests
```python
@pytest.mark.asyncio
async def test_elicitation_protocol():
    """Test that correct MCP elicitation messages are sent."""
    # Mock the underlying MCP transport to verify correct protocol messages
    with patch('fastmcp.transport') as mock_transport:
        # Configure mock to return elicitation response
        mock_transport.send_request.return_value = {
            "action": "accept",
            "data": "test response"
        }

        # Test that tool calls ctx.elicit() correctly
        # Verify correct MCP messages are sent
```

### 4. Business Logic Tests
```python
def test_elicitation_result_handling():
    """Test how tools handle different elicitation results."""
    from fastmcp.elicitation import ElicitationResult

    def handle_result(result: ElicitationResult) -> str:
        if result.action == "accept":
            return f"Got: {result.data}"
        elif result.action == "decline":
            return "User declined"
        else:
            return "User cancelled"

    # Test all result types
    assert handle_result(ElicitationResult(action="accept", data="test")) == "Got: test"
    assert handle_result(ElicitationResult(action="decline")) == "User declined"
    assert handle_result(ElicitationResult(action="cancel")) == "User cancelled"
```

## API Design

### 1. No EnrichMCP-Specific Wrapper Needed
Since EnrichMCP context is deprecated, elicitation should use FastMCP's Context directly:

```python
# DON'T create EnrichMCP-specific elicitation wrappers
# DO use FastMCP Context directly in EnrichMCP tools

@app.tool()
async def my_tool(ctx: Context) -> str:  # FastMCP Context, not EnrichContext
    result = await ctx.elicit("Message", response_type=str)
    return result.data if result.action == "accept" else "No data"
```

### 2. Helper Functions (Optional)
```python
from enrichmcp.elicitation import elicit_or_default

@app.tool()
async def my_tool(ctx: Context) -> str:
    # Optional helper for common patterns
    name = await elicit_or_default(
        ctx,
        "Enter your name:",
        response_type=str,
        default="Anonymous"
    )
    return f"Hello {name}"
```

## Client Requirements

### 1. MCP Client Support
- Client must implement MCP elicitation protocol
- Client must handle structured response types
- Client must provide UI for user input collection

### 2. Response Type Handling
- Simple types: text input, number input, boolean checkboxes
- Constrained types: dropdown/radio buttons
- Structured types: form generation from Pydantic models

### 3. Error Scenarios
- Client doesn't support elicitation → `NotImplementedError`
- User cancels → `action="cancel"`
- User declines → `action="decline"`
- Network/protocol errors → appropriate exceptions

## Examples and Use Cases

### 1. Data Collection
```python
@app.tool()
async def collect_customer_info(ctx: Context) -> Customer:
    """Collect customer information interactively."""
    result = await ctx.elicit(
        "Please provide customer details:",
        response_type=Customer
    )

    if result.action == "accept":
        return result.data
    else:
        raise ValueError(f"Customer info not provided: {result.action}")
```

### 2. Confirmation Workflows
```python
@app.tool()
async def delete_user(user_id: int, ctx: Context) -> dict:
    """Delete user with confirmation."""
    result = await ctx.elicit(
        f"Are you sure you want to delete user {user_id}?",
        response_type=None  # Just approval/rejection
    )

    if result.action == "accept":
        # Perform deletion
        return {"deleted": True, "user_id": user_id}
    else:
        return {"deleted": False, "reason": result.action}
```

### 3. Dynamic Filtering
```python
@app.tool()
async def search_products(ctx: Context) -> list[Product]:
    """Search products with interactive filtering."""
    category_result = await ctx.elicit(
        "Select product category:",
        response_type=Literal["electronics", "clothing", "books", "all"]
    )

    if category_result.action == "accept":
        category = category_result.data
        # Apply filtering based on selection
        return await filter_products_by_category(category)
    else:
        # Return all products if user doesn't specify
        return await get_all_products()
```

## Migration Path

### 1. Phase 1: Cleanup (This PR)
- Delete `tests/test_elicitation.py`
- Remove elicitation documentation from `docs/api/context.md`
- Remove TODO item about elicitation
- Create this implementation plan

### 2. Phase 2: Implementation (Future PR)
- Implement elicitation examples using FastMCP Context
- Add proper integration tests
- Update documentation with working examples
- Add helper functions if needed

### 3. Phase 3: Advanced Features (Future)
- Complex form generation from Pydantic models
- Validation and error handling improvements
- Advanced UI hints for different input types
- Caching of elicitation results

## Files to Modify

### Immediate Cleanup (This PR)
1. **DELETE**: `tests/test_elicitation.py` - Remove fake tests
2. **MODIFY**: `docs/api/context.md` - Remove lines 94-119 (elicitation section)
3. **MODIFY**: `TODO` - Remove line 3 about checking elicitation
4. **CREATE**: `elicitation_plan.md` - This comprehensive plan

### Future Implementation (Separate PR)
1. **CREATE**: `examples/elicitation/` - Working examples
2. **CREATE**: `tests/test_elicitation_integration.py` - Real tests
3. **MODIFY**: `docs/` - Add working elicitation documentation
4. **OPTIONAL**: `src/enrichmcp/elicitation.py` - Helper functions

## Key Differences from Original Plan

1. **No EnrichMCP Context Wrapper** - Use FastMCP Context directly since EnrichMCP context is deprecated
2. **Simpler Integration** - No need for complex context management since we use FastMCP's system
3. **Focus on FastMCP Compatibility** - Ensure elicitation works within EnrichMCP's tool system but uses FastMCP's context
4. **Cleaner Architecture** - Avoid creating unnecessary abstractions over FastMCP's elicitation system

This plan acknowledges that EnrichMCP has moved away from custom context management and now relies on FastMCP's context system directly, making elicitation implementation much more straightforward.
