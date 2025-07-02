# EnrichMCP Examples

This directory contains examples demonstrating how to use EnrichMCP.

-Available examples:

- [hello_world](hello_world) - minimal "Hello, World" API
- [hello_world_http](hello_world_http) - HTTP version using streamable HTTP
- [shop_api](shop_api) - in-memory shop with relationships
- [shop_api_sqlite](shop_api_sqlite) - SQLite-backed shop
- [sqlalchemy_shop](sqlalchemy_shop) - SQLAlchemy ORM version
- [shop_api_gateway](shop_api_gateway) - gateway in front of FastAPI
- [mutable_crud](mutable_crud) - mutable fields and CRUD decorators
- [basic_memory](basic_memory) - simple note-taking API using FileMemoryStore
- [caching](caching) - request caching with ContextCache
- [openai_chat_agent](openai_chat_agent) - interactive chat client

## Hello World

The simplest EnrichMCP application with a single resource that returns "Hello, World!".

```bash
cd hello_world
python app.py
```

## Hello World HTTP

A variant of the Hello World example that serves the API over HTTP using the
streamable HTTP transport.

```bash
cd hello_world_http
python app.py
```

Invoke the example using `mcp_use`:

```bash
python client.py
```

## Shop API

A comprehensive e-commerce API with multiple entities (users, orders and products).

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

A database-backed version of the shop API using SQLite.

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

Both shop examples provide the same functionality but showcase different pagination strategies.

## SQLAlchemy Shop API

A version of the shop example built with SQLAlchemy ORM models. All entities are
declared using SQLAlchemy and registered through `include_sqlalchemy_models`,
which automatically creates CRUD endpoints and relationship resolvers. The
`sqlalchemy_lifespan` helper manages the async engine, seeds the SQLite
database on first run, and removes the file on shutdown when using
`cleanup_db_file=True`.

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

A gateway example that forwards all requests to a FastAPI backend.

```bash
cd shop_api_gateway
uvicorn server:app --port 8001 &
python app.py
```

Stop the background server when finished. The gateway listens on port 8000 and
provides the same schema-driven interface as the other examples.

## Mutable CRUD

A minimal API showcasing mutable fields and the new CRUD decorators.

```bash
cd mutable_crud
python app.py
```

Stop the background server when finished. The gateway listens on port 8000 and provides the same schema-driven interface as the other examples.

## OpenAI MCP Chat Agent

An interactive command-line chat agent that connects to one of the examples
via MCP and lets you talk to it with either OpenAI or a local Ollama model.

```bash
cd openai_chat_agent
# install dependencies for the agent using uv
uv pip install -r requirements.txt
# copy the sample environment and optionally set OPENAI_API_KEY
cp .env.example .env
# run the chat agent
uv run app.py
```

Run the above commands from the `openai_chat_agent` directory so that
`config.json` resolves the relative path to the `shop_api` example.

If `OPENAI_API_KEY` is not set the agent defaults to a local Ollama model defined
by `OLLAMA_MODEL` (defaults to `llama3`).
An Ollama server must be running locally when using this mode or the
agent will fail to connect.

### Running Ollama Locally

1. [Install Ollama](https://ollama.com) and ensure the `ollama` command is in
   your `PATH`.
2. Download the desired model (the example uses `llama3.2` by default):

   ```bash
   ollama pull llama3.2
   ```

3. Start the Ollama server in the background before launching the chat agent:

   ```bash
   ollama serve &
   ```

The chat agent will fail to start if the server is not running.
The included configuration starts the `shop_api` example using the MCP
stdio connector so everything runs locally.
This example demonstrates how to use `MCPAgent` with built-in conversation
memory for chatting with your MCP data.
