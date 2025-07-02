"""
Context module for enrichmcp.

Provides a thin wrapper over FastMCP's Context for request handling.
"""

from mcp.server.fastmcp import Context  # pyright: ignore[reportMissingTypeArgument]

from .cache import ContextCache


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
        @app.retrieve
        async def get_user(user_id: int, ctx: EnrichContext) -> User:
            ctx.info(f"Fetching user {user_id}")
            db = ctx.request_context.lifespan_context["db"]
            return await db.get_user(user_id)
    """

    _cache: ContextCache | None = None

    @property
    def cache(self) -> ContextCache:
        if self._cache is None:
            raise ValueError("Cache is not configured")
        return self._cache
