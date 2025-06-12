from unittest.mock import Mock

import pytest
from sqlalchemy import ForeignKey
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
    """Test user model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, info={"description": "ID"})
    name: Mapped[str] = mapped_column(info={"description": "Name"})
    orders: Mapped[list["Order"]] = relationship(
        back_populates="user", info={"description": "Orders"}
    )


class Order(Base):
    """Test order model."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, info={"description": "ID"})
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(back_populates="orders", info={"description": "User"})


async def seed(session: AsyncSession) -> None:
    user = User(id=1, name="Alice")
    order = Order(id=1, user=user)
    session.add_all([user, order])


def create_app():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    lifespan = sqlalchemy_lifespan(Base, engine, seed=seed)
    app = EnrichMCP("Test", "Desc", lifespan=lifespan)
    include_sqlalchemy_models(app, Base)
    return app, lifespan


@pytest.mark.asyncio
async def test_auto_resources_and_resolvers():
    app, lifespan = create_app()
    async with lifespan(app) as ctx:
        session_factory = ctx["session_factory"]
        mock_ctx = Mock(spec=EnrichContext)
        mock_ctx.request_context = Mock()
        mock_ctx.request_context.lifespan_context = {"session_factory": session_factory}

        list_users = app.resources["list_users"]
        result = await list_users(ctx=mock_ctx)
        assert result.total_items == 1
        assert result.items[0].name == "Alice"

        get_user = app.resources["get_user"]
        single = await get_user(user_id=1, ctx=mock_ctx)
        assert single.name == "Alice"

        # Relationship resolver
        get_orders = app.resources["get_userenrichmodel_orders"]
        rel = await get_orders(user_id=1, ctx=mock_ctx)
        assert len(rel) == 1
        assert rel[0].id == 1
