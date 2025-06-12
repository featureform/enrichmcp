from contextlib import asynccontextmanager

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from enrichmcp import EnrichMCP
from enrichmcp.lifespan import combine_lifespans
from enrichmcp.sqlalchemy.lifecycle import sqlalchemy_lifespan
from enrichmcp.sqlalchemy.mixin import EnrichSQLAlchemyMixin


@pytest.mark.asyncio
async def test_combine_lifespans_merges_and_overrides():
    call_order = []

    @asynccontextmanager
    async def first(app: EnrichMCP):
        call_order.append("first")
        yield {"a": 1}

    @asynccontextmanager
    async def second(app: EnrichMCP):
        call_order.append("second")
        yield {"b": 2, "a": 0}

    combined = combine_lifespans(first, second)
    app = EnrichMCP("Test", "Desc")
    async with combined(app) as ctx:
        assert ctx == {"a": 0, "b": 2}
    assert call_order == ["first", "second"]


@pytest.mark.asyncio
async def test_sqlalchemy_lifespan_creates_session_and_seeds():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    class Base(DeclarativeBase):
        pass

    class User(Base, EnrichSQLAlchemyMixin):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)

    seed_called = False

    async def seed(session: AsyncSession) -> None:
        nonlocal seed_called
        session.add(User(id=1))
        seed_called = True

    lifespan = sqlalchemy_lifespan(Base, engine, seed=seed, session_kwargs={"autoflush": False})
    app = EnrichMCP("Test", "Desc")
    async with lifespan(app) as ctx:
        assert seed_called is True
        session_factory = ctx["session_factory"]
        assert session_factory.kw["autoflush"] is False
        async with session_factory() as session:
            result = await session.execute(select(User.id))
            assert result.scalar_one() == 1
