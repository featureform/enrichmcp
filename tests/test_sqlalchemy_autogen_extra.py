from unittest.mock import Mock

import pytest
from sqlalchemy import ForeignKey, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from enrichmcp import EnrichContext, EnrichMCP
from enrichmcp.sqlalchemy import (
    EnrichSQLAlchemyMixin,
    include_sqlalchemy_models,
    sqlalchemy_lifespan,
)


class Base(DeclarativeBase, EnrichSQLAlchemyMixin):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, info={"description": "ID"})
    name: Mapped[str] = mapped_column(info={"description": "Name"})
    orders: Mapped[list["Order"]] = relationship(
        back_populates="user", info={"description": "Orders"}
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, info={"description": "ID"})
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(back_populates="orders", info={"description": "User"})


async def seed(session: AsyncSession) -> None:
    user = User(id=1, name="Alice")
    orders = [Order(id=i, user=user) for i in range(1, 3)]
    session.add_all([user, *orders])


def create_app():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    lifespan = sqlalchemy_lifespan(Base, engine, seed=seed)
    app = EnrichMCP("Test", "Desc", lifespan=lifespan)
    include_sqlalchemy_models(app, Base)
    return app, lifespan


@pytest.mark.asyncio
async def test_relationship_resolver_validation():
    app, lifespan = create_app()
    async with lifespan(app) as ctx:
        session_factory = ctx["session_factory"]
        mock_ctx = Mock(spec=EnrichContext)
        mock_ctx.request_context = Mock()
        mock_ctx.request_context.lifespan_context = {"session_factory": session_factory}

        get_orders = app.resources["get_userenrichmodel_orders"]

        with pytest.raises(ValueError):
            await get_orders(user_id=1, page=0, page_size=1, ctx=mock_ctx)

        empty = await get_orders(page=1, page_size=1, ctx=mock_ctx)
        assert empty.items == []
        assert not empty.has_next


def test_sqlalchemy_lifespan_cleanup(tmp_path):
    db = tmp_path / "db.sqlite"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db}")

    lifespan = sqlalchemy_lifespan(Base, engine, cleanup_db_file=True)
    app = EnrichMCP("Test", "Desc")

    async def run():
        async with lifespan(app) as ctx:
            session_factory = ctx["session_factory"]
            async with session_factory() as session:
                await session.execute(text("SELECT 1"))

    import asyncio

    asyncio.run(run())

    assert not db.exists()
