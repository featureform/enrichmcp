import json
import sys
import textwrap
from pathlib import Path

import pytest
from mcp_use import MCPClient


@pytest.mark.asyncio
async def test_mcp_client_autogen_pagination(tmp_path: Path) -> None:
    script = tmp_path / "app.py"
    script.write_text(
        textwrap.dedent(
            """
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
                orders: Mapped[list["Order"]] = relationship(
                    back_populates="user", info={"description": "Orders"}
                )

            class Order(Base):
                __tablename__ = "orders"
                id: Mapped[int] = mapped_column(primary_key=True, info={"description": "ID"})
                user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
                user: Mapped[User] = relationship(
                    back_populates="orders", info={"description": "User"}
                )

            async def seed(session: AsyncSession) -> None:
                user = User(id=1, name="Alice")
                orders = [Order(id=i, user=user) for i in range(1, 4)]
                session.add_all([user, *orders])

            engine = create_async_engine("sqlite+aiosqlite:///:memory:")
            lifespan = sqlalchemy_lifespan(Base, engine, seed=seed)
            app = EnrichMCP("Test", "Desc", lifespan=lifespan)
            include_sqlalchemy_models(app, Base)

            if __name__ == "__main__":
                app.run()
            """
        )
    )

    config = {"mcpServers": {"app": {"command": sys.executable, "args": [str(script)]}}}
    client = MCPClient(config=config)
    session = await client.create_session("app")

    result = await session.connector.call_tool(
        "get_userenrichmodel_orders",
        {"page": 1, "page_size": 2, "kwargs": {"user_id": 1}},
    )
    data = json.loads(result.content[0].text)
    assert len(data["items"]) == 2
    assert data["has_next"]

    result2 = await session.connector.call_tool(
        "get_userenrichmodel_orders",
        {"page": 2, "page_size": 2, "kwargs": {"user_id": 1}},
    )
    data2 = json.loads(result2.content[0].text)
    assert len(data2["items"]) == 1
    assert not data2["has_next"]

    await client.close_all_sessions()
