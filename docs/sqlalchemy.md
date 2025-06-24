# SQLAlchemy Integration

`include_sqlalchemy_models` automatically converts SQLAlchemy models into
`EnrichModel` entities and registers default resolvers. It works with any
`AsyncEngine`, so you can use PostgreSQL, MySQL, SQLite or any other database
supported by SQLAlchemy.

```python
from enrichmcp import EnrichMCP
from enrichmcp.sqlalchemy import (
    EnrichSQLAlchemyMixin,
    include_sqlalchemy_models,
    sqlalchemy_lifespan,
)
from sqlalchemy import ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")



class Base(DeclarativeBase, EnrichSQLAlchemyMixin):
    pass

# define SQLAlchemy models inheriting from Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    orders: Mapped[list["Order"]] = relationship(back_populates="user")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    total: Mapped[float] = mapped_column()
    user: Mapped[User] = relationship(back_populates="orders")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    price: Mapped[float] = mapped_column()


lifespan = sqlalchemy_lifespan(Base, engine)  # seed optional
app = EnrichMCP("Shop API", "Demo", lifespan=lifespan)
include_sqlalchemy_models(app, Base)
```

The function scans all models inheriting from `Base` and creates:

- `list_<entity>` and `get_<entity>` resources using primary keys.
- Relationship resolvers for each SQLAlchemy relationship.
  - List relationships return `PageResult` and accept `page` and `page_size`
    parameters without performing expensive count queries.
- Pydantic `EnrichModel` classes with descriptions derived from column `info`.

Pagination parameters `page` and `page_size` are available on the generated
`list_*` endpoints and list relationship resolvers.

`sqlalchemy_lifespan` automatically creates tables on startup and yields a
`session_factory` that resolvers can use. Providing a `seed` function is
optional and useful only for loading sample data during development or tests.
If you are using a temporary SQLite file and want it removed on shutdown,
pass `cleanup_db_file=True`.
