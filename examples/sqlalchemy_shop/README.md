# SQLAlchemy Shop API Example

This example demonstrates how to use EnrichMCP with SQLAlchemy ORM models. It's based on the `shop_api_sqlite` example but uses SQLAlchemy for database modeling and queries.

## Features

- SQLAlchemy model definitions with EnrichMCP integration
- Automatic conversion of SQLAlchemy models to EnrichModel representations
- Async SQLAlchemy with SQLite
- Manual implementation of resources and resolvers (auto-generation coming soon)
- Pagination examples (both page-based and cursor-based)
- Relationship handling between entities

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

## Current Limitations

This example currently includes manual implementations of:
- Resource methods (`list_users`, `get_user`, etc.)
- Relationship resolvers (`@UserEntity.orders.resolver`)

In future versions, these will be auto-generated based on SQLAlchemy metadata with configuration options in the column `info` dictionary.

## Next Steps

The SQLAlchemy integration will be enhanced to support:
- Auto-generated CRUD resources based on primary keys
- Automatic relationship resolvers using SQLAlchemy's relationship definitions
- Filtering and sorting based on column metadata
- Advanced pagination with SQLAlchemy query optimization
