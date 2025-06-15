# SQLAlchemy Shop API Example

This example demonstrates how to use EnrichMCP with SQLAlchemy ORM models. It's based on the `shop_api_sqlite` example but uses SQLAlchemy for database modeling and queries.

## Features

- SQLAlchemy model definitions with EnrichMCP integration
- Automatic conversion of SQLAlchemy models to EnrichModel representations
- Async SQLAlchemy with SQLite
- Automatic creation of CRUD resources and relationship resolvers
- Pagination examples using the generated list endpoints

## Models

The example includes four main models:

1. **User** - Shop customers with orders
2. **Product** - Items available for purchase
3. **Order** - Customer orders with status tracking
4. **OrderItem** - Individual items within orders

## Key Differences from shop_api_sqlite

1. **SQLAlchemy Models**: Uses declarative SQLAlchemy models instead of manual SQL
2. **Type Safety**: SQLAlchemy provides better type safety and relationship handling
3. **Automatic Schema**: Tables are created automatically from model definitions
4. **ORM Benefits**: Lazy loading, eager loading options, and query building

## Running the Example

1. Install dependencies:
```bash
pip install enrichmcp[sqlalchemy]
pip install aiosqlite  # For async SQLite support
```

2. Run the application:
```bash
python app.py
```

The app will:
- Create the SQLite database (`shop.db`) if it doesn't exist
- Create all tables based on the SQLAlchemy models
- Seed sample data on first run
- Start the MCP server

The lifecycle is managed using the `sqlalchemy_lifespan` helper from
`enrichmcp.sqlalchemy`, which provides a session factory to all resources.
Passing `cleanup_db_file=True` removes the `shop.db` file when the app shuts
down.

## Automatic Endpoints

All CRUD resources (`list_*` and `get_*`) along with relationship resolvers are
created automatically via `include_sqlalchemy_models`. The column `info`
dictionary supplies descriptions for the generated endpoints.
