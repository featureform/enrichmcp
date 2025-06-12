# EnrichMCP Examples

This directory contains examples demonstrating how to use EnrichMCP.

## Hello World

The simplest possible EnrichMCP application with a single resource that returns "Hello, World!".

To run this example:

```bash
cd hello_world
python app.py
```

## Shop API

A comprehensive e-commerce shop API with multiple entities (users, orders, products) and relationships.

To run this example:

```bash
cd shop_api
python app.py
```

This example demonstrates:
- Creating multiple entity models with rich descriptions
- Defining relationships between entities
- Page-based pagination for listing orders
- Fraud detection patterns and risk scoring
- In-memory data with filtering capabilities

## Shop API with SQLite

A database-backed version of the shop API using SQLite with real persistence.

To run this example:

```bash
cd shop_api_sqlite
python app.py
```

This example demonstrates:
- Database integration with SQLite
- Cursor-based pagination for efficient data streaming
- Lifespan management for database connections
- Dynamic sample data generation
- Real database queries with relationships

Both shop examples include the same core functionality but demonstrate different pagination strategies - page-based for in-memory data and cursor-based for database queries.

## SQLAlchemy Shop API

A version of the shop example built with SQLAlchemy ORM models. All entities are
declared using SQLAlchemy and registered through `include_sqlalchemy_models`,
which automatically creates CRUD endpoints and relationship resolvers. The
`sqlalchemy_lifespan` helper manages the async engine and seeds the SQLite
database on first run.

To run this example:

```bash
cd sqlalchemy_shop
pip install -r requirements.txt
python app.py
```

This example demonstrates:
- Automatic conversion of SQLAlchemy models to EnrichMCP entities
- Auto-generated CRUD resources and relationship resolvers
- Async database access via SQLAlchemy
- Database seeding and pagination using the generated endpoints

## Shop API Gateway

A version of the shop API that forwards all requests to a separate FastAPI
backend. This demonstrates using EnrichMCP as a lightweight API gateway.

```bash
cd shop_api_gateway
uvicorn server:app --port 8001 &
python app.py
```

Stop the background server when finished. The gateway listens on port 8000 and
provides the same schema-driven interface as the other examples.