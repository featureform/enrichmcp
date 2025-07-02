# Repository Overview: EnrichMCP

This document summarizes the structure, purpose, and usage patterns found in the **enrichmcp** repository. The project provides a framework that exposes structured data models to AI agents via the Model Context Protocol (MCP). Below is a detailed look at the repository's key components, build instructions, examples, and development practices.

## 1. Purpose and Scope

The README describes EnrichMCP as *"The ORM for AI Agents - Turn your data model into a semantic MCP layer"* and highlights its goals:
- generate typed tools from data models
- manage relationships between entities
- provide schema discovery for AI agents
- validate inputs and outputs using Pydantic
- support any backend data source

These points appear in the README between lines 11 and 21【F:README.md†L11-L21】.

The framework allows developers to define Pydantic models (entities) and relationships, register them with an `EnrichMCP` application, and automatically expose resources for AI consumption. It also offers optional SQLAlchemy integration to convert existing ORM models into EnrichMCP entities.

## 2. Project Layout

```
/ (repo root)
├── README.md          – introduction and quickstart
├── Makefile           – common development commands
├── pyproject.toml     – package metadata and tooling config
├── docs/              – user documentation (MkDocs site)
├── examples/          – runnable examples
├── src/enrichmcp/     – library implementation
└── tests/             – unit tests
```

### 2.1 Important Files
- `pyproject.toml` defines project metadata, required Python version, dependencies, optional dev tools, and tooling configuration including Ruff, Pyright, and coverage settings【F:pyproject.toml†L1-L159】.
- `Makefile` contains tasks for setup, linting, tests, docs, and CI usage. For example, running `make setup` creates a virtual environment and installs dependencies【F:Makefile†L18-L24】.
- `docs/` hosts Markdown guides describing core concepts, examples, pagination, and SQLAlchemy integration. The site is served via MkDocs.
- `src/enrichmcp/` implements the framework’s core logic. Modules include:
  - `app.py` – the main `EnrichMCP` application class.
  - `entity.py` – base `EnrichModel` providing serialization and description helpers.
  - `relationship.py` – descriptor for defining relationships and registering resolvers.
  - `pagination.py` – helper classes (`PageResult`, `CursorResult`, etc.).
  - `context.py` – thin wrapper around FastMCP’s context object.
  - `lifespan.py` – helper to combine async lifespans.
  - `sqlalchemy/` – optional SQLAlchemy integration utilities.
- `examples/` demonstrates usage patterns such as a hello world API, a shop API (in-memory and SQLite backed), an OpenAI chat agent, and SQLAlchemy integration.

## 3. Core Library

### 3.1 EnrichMCP Application
`src/enrichmcp/app.py` defines the `EnrichMCP` class. Important behaviors include:
- On initialization, it stores metadata and creates a `FastMCP` instance【F:src/enrichmcp/app.py†L41-L53】.
- Built‑in resource `explore_data_model` provides a comprehensive description of all registered entities, relationships, and usage hints【F:src/enrichmcp/app.py†L64-L98】.
- The `entity` decorator validates that models have descriptions and that all fields (except relationships) include `Field(..., description="...")`. Registered relationships are attached to the model class for later resolution【F:src/enrichmcp/app.py†L100-L173】.
- The `describe_model` method generates documentation describing each entity, its fields, and relationships【F:src/enrichmcp/app.py†L188-L263】.
- The `resource` decorator wraps functions as MCP resources, requiring descriptions and registering them with FastMCP【F:src/enrichmcp/app.py†L265-L325】.
- Before running the server, `run()` validates that all relationships have at least one resolver, raising a `ValueError` otherwise【F:src/enrichmcp/app.py†L327-L358】.

### 3.2 Entities and Relationships
`src/enrichmcp/entity.py` defines `EnrichModel`, a Pydantic BaseModel with additional helpers:
- Relationship fields are detected via `relationship_fields()` and removed from serialized output to prevent recursion【F:src/enrichmcp/entity.py†L31-L66】.
- The `describe()` method returns a Markdown formatted description including fields and relationships【F:src/enrichmcp/entity.py†L67-L128】.

`src/enrichmcp/relationship.py` implements the `Relationship` descriptor used to declare connections between entities. Key features:
- Supports resolver registration via `@Entity.field.resolver` which automatically creates MCP resources with descriptive names and docstrings【F:src/enrichmcp/relationship.py†L58-L105】.
- Validates that resolver return types match the annotated relationship type【F:src/enrichmcp/relationship.py†L112-L133】.

### 3.3 Pagination Utilities
`src/enrichmcp/pagination.py` defines paginated result types:
- `PageResult` for page-number based pagination, including methods to compute `has_previous` and `total_pages`【F:src/enrichmcp/pagination.py†L28-L67】.
- `CursorResult` for cursor-based pagination with `has_next` detection and next-page parameters【F:src/enrichmcp/pagination.py†L72-L100】.
- `PaginationParams` and `CursorParams` provide helper parameters for implementing pagination in resources and resolvers【F:src/enrichmcp/pagination.py†L103-L126】.

### 3.4 SQLAlchemy Integration
The `sqlalchemy` package contains helpers to automatically convert SQLAlchemy models into EnrichMCP entities and register default resources and relationship resolvers. The module exports `EnrichSQLAlchemyMixin`, `include_sqlalchemy_models`, and `sqlalchemy_lifespan` for database setup【F:src/enrichmcp/sqlalchemy/__init__.py†L1-L13】.

## 4. Documentation
The `docs/` directory provides extensive user guides. The main landing page highlights the project’s purpose and quick example usage, demonstrating how to define entities, relationships, resolvers, and resources【F:docs/index.md†L1-L27】. Other documents cover core concepts, pagination strategies, SQLAlchemy integration, and multiple examples with code snippets.

## 5. Examples
The `examples/` folder hosts runnable demonstrations. The `README` lists available examples such as `hello_world`, `shop_api`, `shop_api_sqlite`, `sqlalchemy_shop`, `shop_api_gateway`, and a CLI chat agent. Each demonstrates different features from basic entity definitions to SQLAlchemy auto-generation and API gateway patterns【F:examples/README.md†L1-L36】【F:examples/README.md†L56-L101】.

## 6. Testing and Development
Unit tests under `tests/` verify application behavior including entity registration, resource decoration, pagination utilities, and model description generation. The `Makefile` exposes commands for linting, testing, and docs building. Running `make test` executes pytest with coverage reports【F:Makefile†L45-L47】.

Development tools are configured via `pyproject.toml`, using Ruff for formatting and linting and Pyright for type checking. Coverage settings track code within `src/enrichmcp`【F:pyproject.toml†L94-L160】.

## 7. Contributing
The repository includes a `CONTRIBUTING.md` file and references standard open-source contribution guidelines. The README encourages contributions and notes the project is Apache 2.0 licensed【F:README.md†L107-L118】.

## 8. Summary
EnrichMCP provides a structured approach to exposing data models to AI agents using the Model Context Protocol. It emphasizes rich descriptions, typed relationships, and automatic schema discovery, acting similarly to an ORM but focused on agentic data access. Optional SQLAlchemy integration allows rapid conversion of existing models. Comprehensive documentation, examples, and tests make it straightforward to adopt and extend.

## 9. Agent Setup Instructions

When working on pull requests in this repository, follow these steps to ensure tests run properly:

1. Ensure Python 3.11 is available.
2. Run `make setup` to create a `.venv` and install dependencies in editable mode (`pip install -e .[dev]`).
3. Activate the environment with `source .venv/bin/activate`.
4. Execute the test suite using `make test`.

These commands install all required packages, including development extras and pre-commit hooks, so subsequent commands run without additional setup.
