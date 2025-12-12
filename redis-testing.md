# Redis Integration Testing Plan

## Overview

This document outlines the testing strategy for Redis search integration in EnrichMCP, focusing on local development and CI/CD testing approaches that provide comprehensive coverage without requiring external Redis infrastructure.

## Testing Architecture

### 1. Test Environment Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Testing Pyramid                         │
├─────────────────────────────────────────────────────────────┤
│  E2E Tests          │ Docker Redis + Real MCP Protocol     │
├─────────────────────────────────────────────────────────────┤
│  Integration Tests  │ Redis Container + EnrichMCP App      │
├─────────────────────────────────────────────────────────────┤
│  Unit Tests         │ Mock Redis + Field Metadata Tests    │
└─────────────────────────────────────────────────────────────┘
```

### 2. Local Development Setup

**Prerequisites:**
- Docker and Docker Compose
- Python 3.11+
- pytest and pytest-asyncio

**Redis Test Infrastructure:**
```yaml
# docker-compose.test.yml
version: '3.8'
services:
  redis-test:
    image: redis/redis-stack:latest  # Includes RedisSearch
    ports:
      - "6380:6379"  # Different port to avoid conflicts
    environment:
      - REDIS_ARGS=--save ""  # Disable persistence for tests
    tmpfs:
      - /data  # In-memory storage for speed

  redis-cluster-test:
    image: redis/redis-stack:latest
    ports:
      - "6381:6379"
    environment:
      - REDIS_ARGS=--save ""
    tmpfs:
      - /data
```

## Testing Strategy

### 1. Unit Tests (Fast, No External Dependencies)

**File: `tests/redis/test_field_metadata.py`**
```python
class TestEnrichFieldMetadata:
    def test_field_with_text_index(self):
        """Test EnrichField creates proper text search metadata."""

    def test_field_with_vector_index(self):
        """Test EnrichField creates proper vector search metadata."""

    def test_field_with_multiple_indexes(self):
        """Test EnrichField supports hybrid indexing like ['tag', 'text']."""

    def test_field_metadata_serialization(self):
        """Test search metadata is properly stored in json_schema_extra."""
```

**File: `tests/redis/test_schema_generation.py`**
```python
class TestRedisSchemaGeneration:
    def test_generate_redis_schema_from_model(self):
        """Test Redis FT.CREATE schema generation from EnrichModel."""

    def test_schema_field_mapping(self):
        """Test field types map correctly to Redis field types."""

    def test_schema_with_relationships(self):
        """Test schema generation handles relationship fields properly."""
```

### 2. Integration Tests (Medium Speed, Docker Redis)

**File: `tests/redis/test_redis_integration.py`**
```python
@pytest.fixture(scope="session")
async def redis_container():
    """Start Redis container for integration tests."""
    # Use testcontainers-python or docker-py
    container = await start_redis_container()
    yield container
    await container.stop()

class TestRedisIntegration:
    async def test_index_creation(self, redis_container):
        """Test FT.CREATE commands work with real Redis."""

    async def test_document_storage_and_search(self, redis_container):
        """Test storing and searching documents."""

    async def test_vector_search_operations(self, redis_container):
        """Test vector similarity search with real embeddings."""

    async def test_complex_queries(self, redis_container):
        """Test combined text + filter + vector queries."""

### 3. End-to-End Tests (Slower, Full Stack)

**File: `tests/redis/test_e2e_mcp.py`**
```python
class TestMCPRedisE2E:
    async def test_auto_generated_search_tools(self, redis_container):
        """Test MCP tools are auto-generated from EnrichField metadata."""

    async def test_mcp_tool_execution(self, redis_container):
        """Test MCP tools execute Redis queries correctly."""

    async def test_relationship_traversal(self, redis_container):
        """Test relationship resolvers work with Redis backend."""

## Local Testing Commands

### Quick Development Loop
```bash
# Start Redis for development
docker-compose -f docker-compose.test.yml up -d redis-test

# Run unit tests (fast)
pytest tests/redis/test_field_metadata.py -v

# Run integration tests (medium)
pytest tests/redis/test_redis_integration.py -v

# Run full E2E suite (slow)
pytest tests/redis/test_e2e_mcp.py -v

# Cleanup
docker-compose -f docker-compose.test.yml down
```

### Test Data Management
```bash
# Reset Redis between test runs
docker exec redis-test redis-cli FLUSHALL

# Inspect Redis state during debugging
docker exec -it redis-test redis-cli
> FT._LIST  # List all indexes
> FT.INFO stock_idx  # Inspect specific index
> JSON.GET stock:AAPL  # Check document storage
```

## Test Implementation Details

### 1. Redis Container Management

**File: `tests/redis/conftest.py`**
```python
import pytest
import docker
import redis.asyncio as redis
from testcontainers.redis import RedisContainer

@pytest.fixture(scope="session")
async def redis_test_container():
    """Manage Redis container lifecycle for tests."""
    with RedisContainer("redis/redis-stack:latest") as container:
        container.with_exposed_ports(6379)
        container.start()

        # Wait for Redis to be ready
        client = redis.from_url(container.get_connection_url())
        await client.ping()

        yield container

        await client.close()

@pytest.fixture
async def clean_redis(redis_test_container):
    """Clean Redis state between tests."""
    client = redis.from_url(redis_test_container.get_connection_url())
    await client.flushall()
    yield client
    await client.close()
```

### 2. Sample Test Models

**File: `tests/redis/fixtures/test_models.py`**
```python
from enrichmcp import EnrichModel, EnrichField, Relationship

class TestProduct(EnrichModel):
    """Test model with various Redis field types."""

    id: str = EnrichField(
        description="Product ID",
        index="primary"
    )

    name: str = EnrichField(
        description="Product name",
        index="text"
    )

    category: str = EnrichField(
        description="Product category",
        index="tag"
    )

    price: float = EnrichField(
        description="Product price",
        index="numeric"
    )

    description_embedding: list[float] = EnrichField(
        description="Product description embedding",
        index="vector",
        vector_dim=128,
        distance_metric="cosine"
    )

    tags: list[str] = EnrichField(
        description="Product tags",
        index=["tag", "text"]  # Hybrid indexing
    )
```

### 3. Performance Testing

**File: `tests/redis/test_performance.py`**
```python
class TestRedisPerformance:
    async def test_bulk_indexing_performance(self, clean_redis):
        """Test performance of bulk document indexing."""

    async def test_search_query_performance(self, clean_redis):
        """Test search query response times."""

    async def test_vector_search_performance(self, clean_redis):
        """Test vector similarity search performance."""

    async def test_concurrent_operations(self, clean_redis):
        """Test concurrent read/write operations."""
```

## CI/CD Integration

### GitHub Actions Workflow
```yaml
# .github/workflows/redis-tests.yml
name: Redis Integration Tests

on: [push, pull_request]

jobs:
  redis-tests:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis/redis-stack:latest
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[dev,redis]"

      - name: Run Redis integration tests
        run: |
          pytest tests/redis/ -v --redis-url redis://localhost:6379
        env:
          REDIS_URL: redis://localhost:6379
```

## Testing Best Practices

### 1. Test Isolation
- Each test gets a clean Redis instance
- Use unique key prefixes per test
- Clean up indexes and data after each test

### 2. Realistic Test Data
- Use actual embedding vectors (small dimension for speed)
- Test with realistic document sizes and quantities
- Include edge cases (empty strings, null values, large arrays)

### 3. Error Handling Tests
- Test Redis connection failures
- Test invalid query syntax
- Test index creation conflicts
- Test memory/storage limits

### 4. Debugging Support
```python
@pytest.fixture
def redis_debug_info(clean_redis):
    """Provide Redis debugging utilities."""
    async def debug_index(index_name: str):
        info = await clean_redis.ft(index_name).info()
        print(f"Index {index_name}: {info}")

    async def debug_search(index_name: str, query: str):
        results = await clean_redis.ft(index_name).search(query)
        print(f"Query '{query}' returned {len(results.docs)} results")

    return {"debug_index": debug_index, "debug_search": debug_search}
```

## Success Criteria

### Unit Tests
- ✅ Field metadata extraction and validation
- ✅ Schema generation from model definitions
- ✅ Query building and parameter validation
- ✅ Error handling for invalid configurations

### Integration Tests
- ✅ Redis index creation and management
- ✅ Document storage and retrieval
- ✅ All search types (text, tag, numeric, vector)
- ✅ Complex multi-field queries
- ✅ Performance within acceptable limits

### E2E Tests
- ✅ MCP tool auto-generation
- ✅ Tool execution with Redis backend
- ✅ Relationship traversal
- ✅ Error propagation to MCP clients

## Makefile Integration (Minimal Approach)

The existing Makefile should remain clean and focused. We'll add minimal Redis support that follows existing patterns:

### Option 1: Automatic Container Management (Recommended)

**No Makefile changes needed.** Redis containers are managed automatically by pytest fixtures:

```python
# tests/redis/conftest.py
import pytest
from testcontainers.redis import RedisContainer

@pytest.fixture(scope="session")
def redis_container():
    """Auto-start Redis container when running Redis tests."""
    with RedisContainer("redis/redis-stack:latest") as container:
        container.with_exposed_ports(6379)
        yield container

@pytest.fixture(scope="function")
async def clean_redis(redis_container):
    """Clean Redis state between tests."""
    import redis.asyncio as redis
    client = redis.from_url(redis_container.get_connection_url())
    await client.flushall()
    yield client
    await client.close()
```

**Developer workflow:**
```bash
# Existing commands work unchanged
make test                    # Runs all tests, Redis starts automatically when needed
make test tests/redis/       # Run only Redis tests
make test -k "redis"         # Run tests matching "redis"
```

### Option 2: Minimal Makefile Addition

If manual container control is preferred, add just two commands:

```makefile
# Add to existing .PHONY line
.PHONY: setup format lint test examples-test build clean docs docs-format install dev venv ci-setup ci-lint ci-test redis-up redis-down

# Minimal Redis commands
redis-up:
	@docker-compose -f docker-compose.test.yml up -d --wait

redis-down:
	@docker-compose -f docker-compose.test.yml down -v

# Existing test command unchanged - works with or without Redis containers
test:
	$(PYTHON_CMD) -m pytest --cov-report=term --cov-report=html --cov=src/enrichmcp
```

**Developer workflow:**
```bash
# Manual container management
make redis-up               # Start Redis containers
make test tests/redis/      # Run Redis tests
make redis-down             # Stop containers

# Or let tests manage containers automatically
make test                   # Works either way
```

### Docker Compose File (Simple)

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  redis-test:
    image: redis/redis-stack:latest
    ports:
      - "6379:6379"  # Use standard port, assume no conflicts during testing
    environment:
      - REDIS_ARGS=--save ""  # Disable persistence
    tmpfs:
      - /data  # In-memory storage for speed
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
```

### Test Configuration

```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
markers = [
    "redis: marks tests as requiring Redis (deselect with '-m \"not redis\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests"
]

# Skip Redis tests if no Redis available
addopts = "--strict-markers"
```

### Benefits of Minimal Approach

1. **Clean Makefile**: Keeps existing simplicity, adds at most 2 commands
2. **Automatic Management**: Tests handle their own infrastructure needs
3. **Flexible**: Works with or without manual container management
4. **Standard Patterns**: Uses pytest fixtures and markers (common practice)
5. **CI Friendly**: Same commands work locally and in CI

### Debugging Support

```bash
# Access Redis CLI when containers are running
docker exec -it $(docker ps -q --filter ancestor=redis/redis-stack:latest) redis-cli

# Or with docker-compose
docker-compose -f docker-compose.test.yml exec redis-test redis-cli
```

This testing strategy ensures Redis integration works reliably in development, CI/CD, and production environments while maintaining fast feedback loops for developers.
```
