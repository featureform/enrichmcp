"""Context utilities for enrichmcp."""

from mcp.server.fastmcp import Context
from mcp.types import ModelHint, ModelPreferences


def get_enrich_context() -> Context:  # pyright: ignore[reportMissingTypeArgument]
    """Get FastMCP Context directly.

    This function provides a clean way to access FastMCP's Context
    in auto-generated functions or when dependency injection isn't available.

    Uses the standard FastMCP 2.0 pattern: ctx.request_context.lifespan_context
    """
    from fastmcp.server.dependencies import get_context as get_fastmcp_context

    try:
        return get_fastmcp_context()  # pyright: ignore[reportReturnType]
    except RuntimeError:
        # No active context - this should only happen in tests
        raise RuntimeError(
            "No active FastMCP context. This function should only be called "
            "within MCP request handlers. For tests, mock get_context() instead.",
        ) from None


# Legacy alias for backward compatibility
EnrichContext = Context


def prefer_fast_model() -> ModelPreferences:
    """Model preferences optimized for speed and cost using small models."""
    return ModelPreferences(
        hints=[
            ModelHint(name="gpt-4o-mini-20240613"),
            ModelHint(name="claude-3-haiku-20240307"),
            ModelHint(name="llama-3-8b"),
        ],
        costPriority=0.8,
        speedPriority=0.9,
        intelligencePriority=0.3,
    )


def prefer_medium_model() -> ModelPreferences:
    """Balanced model preferences for general use."""
    return ModelPreferences(
        hints=[
            ModelHint(name="gpt-4o-2024-05-13"),
            ModelHint(name="claude-3-sonnet-20240229"),
            ModelHint(name="llama-3-70b"),
        ],
        costPriority=0.5,
        speedPriority=0.6,
        intelligencePriority=0.6,
    )


def prefer_smart_model() -> ModelPreferences:
    """Model preferences optimized for intelligence and capability."""
    return ModelPreferences(
        hints=[
            ModelHint(name="o3"),
            ModelHint(name="claude-3-opus-20240229"),
            ModelHint(name="llama-3-405b"),
        ],
        costPriority=0.2,
        speedPriority=0.3,
        intelligencePriority=0.9,
    )
