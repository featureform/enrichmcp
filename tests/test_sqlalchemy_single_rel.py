from unittest.mock import Mock

import pytest
from fastmcp import Context
from sqlalchemy import ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from enrichmcp import EnrichMCP
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
    order: Mapped["Order"] = relationship(
        back_populates="user",
        uselist=False,
        info={"description": "Order"},
    )


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True, info={"description": "ID"})
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(back_populates="order", info={"description": "User"})


async def seed(session: AsyncSession) -> None:
    user = User(id=1, name="Bob")
    order = Order(id=1, user=user)
    session.add_all([user, order])


def create_app():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    lifespan = sqlalchemy_lifespan(Base, engine, seed=seed)
    app = EnrichMCP("Test", "Desc", lifespan=lifespan)
    include_sqlalchemy_models(app, Base)
    return app, lifespan


@pytest.mark.asyncio
async def test_single_relationship_resolver():
    app, lifespan = create_app()
    async with lifespan(app) as ctx:
        sf = ctx["session_factory"]
        mctx = Mock(spec=Context)
        mctx.request_context = Mock(lifespan_context={"session_factory": sf})
        resolver = app.resources["get_orderenrichmodel_user"]
        user = await resolver.fn(order_id=1, ctx=mctx)
        assert user.name == "Bob"
        none = await resolver.fn(order_id=99, ctx=mctx)
        assert none is None
        # direct parameter call
        again = await resolver.fn(order_id=1, ctx=mctx)
        assert again.name == "Bob"
