"""Default SQLAlchemy lifespan helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)  # pyright: ignore[reportMissingImports,reportAttributeAccessIssue]

from enrichmcp.app import EnrichMCP

if TYPE_CHECKING:
    from sqlalchemy.orm import (
        DeclarativeBase,  # pyright: ignore[reportMissingImports,reportAttributeAccessIssue]
    )

Lifespan = Callable[[EnrichMCP], AbstractAsyncContextManager[dict[str, Any]]]


def sqlalchemy_lifespan(
    base: type[DeclarativeBase],
    engine: AsyncEngine,
    *,
    seed: Callable[[AsyncSession], Awaitable[None]] | None = None,
    session_kwargs: dict[str, Any] | None = None,
    cleanup_db_file: bool = False,
) -> Lifespan:
    """Create a lifespan that sets up tables and yields a session factory."""

    session_kwargs = session_kwargs or {}

    @asynccontextmanager
    async def _lifespan(app: EnrichMCP) -> AsyncIterator[dict[str, Any]]:
        async with engine.begin() as conn:
            await conn.run_sync(base.metadata.create_all)
        session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False, **session_kwargs
        )
        if seed is not None:
            async with session_factory() as session:
                await seed(session)
                await session.commit()
        try:
            yield {"session_factory": session_factory}
        finally:
            await engine.dispose()
            if (
                cleanup_db_file
                and engine.url.database
                and engine.url.drivername.startswith("sqlite")
            ):
                import os

                if os.path.exists(engine.url.database):
                    os.remove(engine.url.database)

    return _lifespan
