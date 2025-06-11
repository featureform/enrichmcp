"""
Context module for enrichmcp.

Provides a thin wrapper over FastMCP's Context for request handling.
"""

from mcp.server.fastmcp import Context  # pyright: ignore[reportMissingTypeArgument]


class EnrichContext(Context):  # pyright: ignore[reportMissingTypeArgument]
    """
    Thin wrapper over FastMCP's Context.

    This context is automatically injected into resource and resolver functions
    that have a parameter typed with EnrichContext. It provides access to:
    - Logging methods (info, debug, warning, error)
    - Progress reporting
    - Resource reading
    - Request metadata
    - Lifespan context (e.g., database connections)

    Example:
        @app.resource
        async def get_user(user_id: int, ctx: EnrichContext) -> User:
            ctx.info(f"Fetching user {user_id}")
            db = ctx.request_context.lifespan_context["db"]
            return await db.get_user(user_id)
    """

    pass
