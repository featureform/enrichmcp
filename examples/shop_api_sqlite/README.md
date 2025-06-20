# Shop API with SQLite Example

This example demonstrates how to use EnrichMCP with a real SQLite database, showcasing:

- **Lifespan management**: Database connection lifecycle
- **Context injection**: Accessing database from resolvers and resources
- **Progress reporting**: Visual feedback during operations
- **Logging**: Structured logging throughout the API

## Features

- SQLite database with automatic schema creation
- Sample data initialization
- Context injection in all resolvers and resources
- Proper error handling and logging
- Progress reporting for long operations

## Running the Example

```bash
python app.py
```

This will:
1. Create a SQLite database (`shop.db`) in the current directory
2. Initialize the schema with tables for users, products, orders
3. Insert sample data if the database is empty
4. Start the MCP server

## How It Works

### Lifespan Management

The `lifespan` async context manager handles database setup and teardown:

```python
@asynccontextmanager
async def lifespan(app: EnrichMCP) -> AsyncIterator[dict[str, Any]]:
    # Setup: Connect to database
    db = Database("shop.db")
    await db.connect()

    # Yield context available in handlers
    yield {"db": db}

    # Cleanup: Close connection
    await db.close()
```

### Context Injection

Resources and resolvers receive context automatically when they have a parameter typed as `EnrichContext`:

```python
@app.retrieve
async def get_user(user_id: int, ctx: EnrichContext) -> User:
    # Access database from lifespan context
    db = ctx.request_context.lifespan_context["db"]

    # Use logging
    await ctx.info(f"Fetching user {user_id}")

    # Query database
    user_row = await db.get_user(user_id)
    return User(**user_row)
```

### Key Differences from Static Example

1. **Real Database**: All data comes from SQLite, not hardcoded lists
2. **Async Operations**: Database operations are async-ready
3. **Context Usage**: Shows logging, progress, and database access
4. **Error Handling**: Proper handling of missing data

## Database Schema

- **users**: Customer accounts with risk scores
- **products**: Items for sale with fraud risk levels
- **orders**: Purchase transactions with status tracking
- **order_products**: Many-to-many relationship between orders and products
