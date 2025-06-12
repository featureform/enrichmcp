# SQLAlchemy Integration

`include_sqlalchemy_models` automatically converts SQLAlchemy models into
`EnrichModel` entities and registers default resolvers.

```python
from enrichmcp import EnrichMCP
from enrichmcp.sqlalchemy import (
    EnrichSQLAlchemyMixin,
    include_sqlalchemy_models,
    sqlalchemy_lifespan,
)
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine("sqlite+aiosqlite:///shop.db")

class Base(DeclarativeBase, EnrichSQLAlchemyMixin):
    pass

# define SQLAlchemy models inheriting from Base

lifespan = sqlalchemy_lifespan(Base, engine)
app = EnrichMCP("Shop API", "Demo", lifespan=lifespan)
include_sqlalchemy_models(app, Base)
```

The function scans all models inheriting from `Base` and creates:

- `list_<entity>` and `get_<entity>` resources using primary keys.
- Relationship resolvers for each SQLAlchemy relationship.
- Pydantic `EnrichModel` classes with descriptions derived from column `info`.

Pagination parameters `page` and `page_size` are available on the generated
`list_*` endpoints.
