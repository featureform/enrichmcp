"""
Context module for enrichmcp.

Provides a thin wrapper over FastMCP's Context for request handling.
"""

from typing import Literal

from mcp.server.fastmcp import Context  # pyright: ignore[reportMissingTypeArgument]
from mcp.types import (
    CreateMessageResult,
    ModelHint,
    ModelPreferences,
    SamplingMessage,
    TextContent,
)

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

    # ------------------------------------------------------------------
    # LLM Integration
    # ------------------------------------------------------------------

    def _convert_messages(
        self, messages: str | list[str | SamplingMessage]
    ) -> list[SamplingMessage]:
        """Convert plain strings to ``SamplingMessage`` objects."""

        if isinstance(messages, str):
            messages = [messages]

        converted: list[SamplingMessage] = []
        for msg in messages:
            if isinstance(msg, SamplingMessage):
                converted.append(msg)
            elif isinstance(msg, str):
                converted.append(
                    SamplingMessage(
                        role="user",
                        content=TextContent(type="text", text=msg),
                    )
                )
            else:
                raise TypeError("messages must be str or SamplingMessage")
        return converted

    async def ask_llm(
        self,
        messages: str | list[str | SamplingMessage],
        *,
        system_prompt: str | None = None,
        max_tokens: int = 1000,
        temperature: float | None = None,
        model_preferences: ModelPreferences | None = None,
        allow_tools: Literal["none", "thisServer", "allServers"] | None = "none",
        stop_sequences: list[str] | None = None,
    ) -> CreateMessageResult:
        """Request LLM sampling via the connected client."""

        sampling_messages = self._convert_messages(messages)
        session = self._request_context.session  # type: ignore[attr-defined]
        return await session.create_message(
            messages=sampling_messages,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model_preferences=model_preferences,
            include_context=allow_tools,
            stop_sequences=stop_sequences,
        )

    async def sampling(
        self,
        messages: str | list[str | SamplingMessage],
        **kwargs,
    ) -> CreateMessageResult:
        """Alias for :meth:`ask_llm`."""

        return await self.ask_llm(messages, **kwargs)


def prefer_fast_model() -> ModelPreferences:
    """Model preferences optimized for speed and cost."""

    return ModelPreferences(
        hints=[ModelHint(name="gpt-4o-mini"), ModelHint(name="claude-3-haiku")],
        costPriority=0.8,
        speedPriority=0.9,
        intelligencePriority=0.3,
    )


def prefer_smart_model() -> ModelPreferences:
    """Model preferences optimized for intelligence and capability."""

    return ModelPreferences(
        hints=[ModelHint(name="gpt-4o"), ModelHint(name="claude-3-opus")],
        costPriority=0.2,
        speedPriority=0.3,
        intelligencePriority=0.9,
    )
