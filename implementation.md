# Redis Search Integration Implementation Plan

## Overview

This document outlines the implementation plan for integrating Redis search capabilities into EnrichMCP using a unified Field approach. The design extends the existing EnrichMCP patterns while maintaining backward compatibility and providing a clean user experience.

## Core Design Principles

1. **Unified Field Approach**: Search capabilities are metadata on regular Pydantic fields, not separate field types
2. **Backward Compatibility**: Existing EnrichMCP code continues to work unchanged
3. **Gradual Adoption**: Users can add search capabilities incrementally
4. **Type Safety**: Full Pydantic validation with Redis search integration
5. **Auto-Generation**: Search resources and schemas generated automatically from field metadata

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RedisModel    │    │   RedisField    │    │ RedisInterface  │
│  (extends       │    │  (enhanced      │    │   (Redis        │
│  EnrichModel)   │◄───┤   Field with    │    │   operations)   │
│                 │    │   search meta)  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Auto-Generated  │    │ Schema Builder  │    │ Query Builder   │
│ Search Tools    │    │ (RQE schemas)   │    │ (Redis queries) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 1. Enhanced Field System

### 1.1 RedisField Function

Create an enhanced `RedisField` function that extends Pydantic's `Field` with search metadata:

```python
# src/enrichmcp/redis/field.py

from typing import Literal, Any, Optional
from pydantic import Field as PydanticField

def RedisField(
    *,
    description: str,
    # Standard Pydantic field options
    default: Any = PydanticUndefined,
    json_schema_extra: dict | None = None,

    # Redis search options
    search_type: Literal["text", "tag", "numeric", "geo", "vector"] | None = None,

    # Key component option
    key_component: bool = False,

    # Text search options
    searchable: bool = False,
    weight: float = 1.0,
    no_stem: bool = False,
    phonetic_matcher: str | None = None,

    # Tag/filtering options
    filterable: bool = False,
    case_sensitive: bool = False,
    separator: str = ",",

    # Numeric options
    sortable: bool = False,

    # Vector options
    dims: int | None = None,
    algorithm: Literal["flat", "hnsw"] = "hnsw",
    distance_metric: Literal["cosine", "l2", "ip"] = "cosine",

    # HNSW specific
    m: int = 16,
    ef_construction: int = 200,
    ef_runtime: int = 10,

    **kwargs
) -> Any:
    """Enhanced Field with Redis search capabilities."""

    # Build search metadata
    search_config = {}
    if search_type:
        search_config.update({
            "type": search_type,
            "searchable": searchable,
            "weight": weight,
            "no_stem": no_stem,
            "phonetic_matcher": phonetic_matcher,
            "filterable": filterable,
            "case_sensitive": case_sensitive,
            "separator": separator,
            "sortable": sortable,
            "dims": dims,
            "algorithm": algorithm,
            "distance_metric": distance_metric,
            "m": m,
            "ef_construction": ef_construction,
            "ef_runtime": ef_runtime,
        })

    # Add key component flag
    if key_component:
        search_config["key_component"] = True

    # Merge with existing json_schema_extra
    extra = json_schema_extra or {}
    if search_config:
        extra["redis_search"] = search_config

    return PydanticField(
        default=default,
        description=description,
        json_schema_extra=extra,
        **kwargs
    )
```

### 1.2 Field Detection and Metadata

Extend field detection to identify Redis search fields:

```python
# In RedisModel class methods

@classmethod
def redis_search_fields(cls) -> dict[str, dict]:
    """Return fields with Redis search metadata."""
    search_fields = {}
    for name, field in cls.model_fields.items():
        if name in cls.relationship_fields():
            continue

        extra = getattr(field, "json_schema_extra", {})
        search_config = extra.get("redis_search")
        if search_config:
            search_fields[name] = search_config

    return search_fields

@classmethod
def key_component_fields(cls) -> set[str]:
    """Return fields marked as key components (excluded from storage)."""
    key_fields = set()
    for name, field in cls.model_fields.items():
        extra = getattr(field, "json_schema_extra", {})
        search_config = extra.get("redis_search", {})
        if search_config.get("key_component", False):
            key_fields.add(name)
    return key_fields

@classmethod
def redis_prefix(cls) -> str:
    """Extract Redis prefix from key template."""
    template = getattr(cls, '__redis_key__', f"{cls.__name__.lower()}:{{id}}")
    # Extract everything before first {
    return template.split('{')[0]

def redis_key(self) -> str:
    """Generate Redis key for this instance."""
    template = getattr(self.__class__, '__redis_key__', f"{self.__class__.__name__.lower()}:{{id}}")
    return template.format(**self.model_dump(exclude=set()))

@classmethod
def get_redis_schema(cls) -> dict:
    """Generate Redis RQE schema for this model."""
    schema_fields = []

    # Only include non-key-component fields in the index
    search_fields = cls.redis_search_fields()
    key_fields = cls.key_component_fields()

    for field_name, config in search_fields.items():
        # Skip key component fields - they're not stored in JSON
        if field_name in key_fields:
            continue

        field_def = {"name": field_name}

        if config["type"] == "text" and config["searchable"]:
            field_def.update({
                "type": "TEXT",
                "weight": config["weight"],
                "sortable": config["sortable"],
                "no_stem": config["no_stem"]
            })
            if config["phonetic_matcher"]:
                field_def["phonetic"] = config["phonetic_matcher"]

        elif config["type"] == "tag" and config["filterable"]:
            field_def.update({
                "type": "TAG",
                "separator": config["separator"],
                "case_sensitive": config["case_sensitive"],
                "sortable": config["sortable"]
            })

        elif config["type"] == "numeric":
            field_def.update({
                "type": "NUMERIC",
                "sortable": config["sortable"]
            })

        elif config["type"] == "vector":
            field_def.update({
                "type": "VECTOR",
                "algorithm": config["algorithm"].upper(),
                "dims": config["dims"],
                "distance_metric": config["distance_metric"].upper(),
                "datatype": "FLOAT32"
            })
            if config["algorithm"] == "hnsw":
                field_def.update({
                    "m": config["m"],
                    "ef_construction": config["ef_construction"]
                })

        schema_fields.append(field_def)

    return {
        "index": {
            "name": f"{cls.__name__.lower()}_idx",
            "prefix": cls.redis_prefix(),
            "storage_type": "json"
        },
        "fields": schema_fields
    }

def model_dump(self, **kwargs):
    """Override to exclude key component fields from storage."""
    key_fields = self.__class__.key_component_fields()
    exclude = kwargs.get('exclude', set())
    if isinstance(exclude, set):
        exclude = exclude | key_fields
    elif isinstance(exclude, dict):
        # Add key fields to exclusion dict
        for field in key_fields:
            exclude[field] = True
    else:
        exclude = key_fields
    kwargs['exclude'] = exclude
    return super().model_dump(**kwargs)
```

## 2. RedisModel Extension

### 2.1 RedisModel Class

Create `RedisModel` that extends `EnrichModel` with Redis search capabilities:

```python
# src/enrichmcp/redis/model.py

from enrichmcp import EnrichModel
from .interface import RedisInterface
from typing import Optional, Any

class RedisModel(EnrichModel):
    """
    Enhanced EnrichModel with Redis search capabilities.

    Extends EnrichModel with automatic Redis indexing, search schema generation,
    and search resource creation based on field metadata.
    """

    # Redis connection (injected by app)
    _redis_interface: Optional[RedisInterface] = None

    @classmethod
    def set_redis_interface(cls, redis_interface: RedisInterface) -> None:
        """Set the Redis interface for this model class."""
        cls._redis_interface = redis_interface

    @classmethod
    def redis_search_fields(cls) -> dict[str, dict]:
        """Return fields with Redis search metadata."""
        # Implementation from above
        pass

    @classmethod
    def get_redis_schema(cls) -> dict:
        """Generate Redis RQE schema for this model."""
        # Implementation from above
        pass

    @classmethod
    async def create_redis_index(cls) -> None:
        """Create Redis search index for this model."""
        if not cls._redis_interface:
            raise RuntimeError("Redis interface not configured")

        schema = cls.get_redis_schema()
        await cls._redis_interface.create_index(schema)

    @classmethod
    async def search_text(
        cls,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        offset: int = 0
    ) -> list["RedisModel"]:
        """Perform full-text search on this model."""
        if not cls._redis_interface:
            raise RuntimeError("Redis interface not configured")

        results = await cls._redis_interface.search_text(
            index_name=f"{cls.__name__.lower()}_idx",
            query=query,
            filters=filters,
            limit=limit,
            offset=offset
        )

        return [cls(**result) for result in results]

    @classmethod
    async def search_vector(
        cls,
        vector: list[float],
        vector_field: str,
        limit: int = 10,
        threshold: float | None = None
    ) -> list["RedisModel"]:
        """Perform vector similarity search on this model."""
        if not cls._redis_interface:
            raise RuntimeError("Redis interface not configured")

        results = await cls._redis_interface.search_vector(
            index_name=f"{cls.__name__.lower()}_idx",
            vector=vector,
            vector_field=vector_field,
            limit=limit,
            threshold=threshold
        )

        return [cls(**result) for result in results]

    async def save_to_redis(self) -> None:
        """Save this instance to Redis with proper indexing."""
        if not self._redis_interface:
            raise RuntimeError("Redis interface not configured")

        # Generate Redis key
        key = f"{self.__class__.__name__.lower()}:{self.id}"

        # Serialize for Redis (exclude relationships)
        data = self.model_dump(exclude=self.relationship_fields())

        await self._redis_interface.save_document(key, data)
```

### 2.2 Model Registration and Index Creation

Extend the app to handle Redis model registration:

```python
# In EnrichMCP app class

async def register_redis_model(
    self,
    model_class: type[RedisModel],
    redis_interface: RedisInterface
) -> None:
    """Register a Redis-enabled model and create its search index."""

    # Set Redis interface on the model
    model_class.set_redis_interface(redis_interface)

    # Create search index
    await model_class.create_redis_index()

    # Auto-generate search resources
    await self._create_search_resources(model_class)

async def _create_search_resources(self, model_class: type[RedisModel]) -> None:
    """Auto-generate search resources for a Redis model."""

    search_fields = model_class.redis_search_fields()

    # Generate text search resource if any text fields exist
    text_fields = [name for name, config in search_fields.items()
                   if config["type"] == "text" and config["searchable"]]

    if text_fields:
        @self.retrieve
        async def search_by_text(
            query: str,
            limit: int = 10,
            offset: int = 0
        ) -> list[model_class]:
            f"""Search {model_class.__name__} by text content."""
            return await model_class.search_text(query, limit=limit, offset=offset)

        # Rename function to be model-specific
        search_by_text.__name__ = f"search_{model_class.__name__.lower()}_by_text"

    # Generate filter resources for tag fields
    tag_fields = [name for name, config in search_fields.items()
                  if config["type"] == "tag" and config["filterable"]]

    for field_name in tag_fields:
        @self.retrieve
        async def filter_by_tag(tag_value: str) -> list[model_class]:
            f"""Filter {model_class.__name__} by {field_name}."""
            filters = {field_name: tag_value}
            return await model_class.search_text("*", filters=filters)

        filter_by_tag.__name__ = f"filter_{model_class.__name__.lower()}_by_{field_name}"

    # Generate vector search resource if vector fields exist
    vector_fields = [name for name, config in search_fields.items()
                     if config["type"] == "vector"]

    for field_name in vector_fields:
        @self.retrieve
        async def search_similar(
            vector: list[float],
            limit: int = 10,
            threshold: float = 0.8
        ) -> list[model_class]:
            f"""Find {model_class.__name__} similar to the given vector."""
            return await model_class.search_vector(
                vector=vector,
                vector_field=field_name,
                limit=limit,
                threshold=threshold
            )

        search_similar.__name__ = f"find_similar_{model_class.__name__.lower()}"
```

## 3. Redis Interface Layer

### 3.1 Abstract Redis Interface

Define an abstract interface for Redis operations:

```python
# src/enrichmcp/redis/interface.py

from abc import ABC, abstractmethod
from typing import Any, Optional

class RedisInterface(ABC):
    """Abstract interface for Redis search operations."""

    @abstractmethod
    async def create_index(self, schema: dict) -> None:
        """Create a search index from schema definition."""
        pass

    @abstractmethod
    async def save_document(self, key: str, document: dict) -> None:
        """Save a document to Redis with proper indexing."""
        pass

    @abstractmethod
    async def search_text(
        self,
        index_name: str,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        offset: int = 0
    ) -> list[dict]:
        """Perform full-text search."""
        pass

    @abstractmethod
    async def search_vector(
        self,
        index_name: str,
        vector: list[float],
        vector_field: str,
        limit: int = 10,
        threshold: float | None = None
    ) -> list[dict]:
        """Perform vector similarity search."""
        pass

    @abstractmethod
    async def filter_by_tags(
        self,
        index_name: str,
        filters: dict[str, Any],
        limit: int = 10,
        offset: int = 0
    ) -> list[dict]:
        """Filter documents by tag fields."""
        pass

    @abstractmethod
    async def delete_document(self, key: str) -> None:
        """Delete a document from Redis."""
        pass

    @abstractmethod
    async def get_document(self, key: str) -> dict | None:
        """Retrieve a document by key."""
        pass
```

### 3.2 Redis Implementation

Concrete implementation using redis-py:

```python
# src/enrichmcp/redis/redis_impl.py

import redis.asyncio as redis
from redis.commands.search import Search
from redis.commands.search.field import TextField, TagField, NumericField, VectorField
from redis.commands.search.query import Query
from .interface import RedisInterface

class RedisSearchInterface(RedisInterface):
    """Redis implementation using redis-py and RediSearch."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        self.search = Search(self.redis)

    async def create_index(self, schema: dict) -> None:
        """Create RediSearch index from schema."""
        index_name = schema["index"]["name"]
        prefix = schema["index"]["prefix"]

        # Convert schema fields to redis-py field objects
        fields = []
        for field_def in schema["fields"]:
            if field_def["type"] == "TEXT":
                field = TextField(
                    field_def["name"],
                    weight=field_def.get("weight", 1.0),
                    sortable=field_def.get("sortable", False),
                    no_stem=field_def.get("no_stem", False)
                )
            elif field_def["type"] == "TAG":
                field = TagField(
                    field_def["name"],
                    separator=field_def.get("separator", ","),
                    case_sensitive=field_def.get("case_sensitive", False),
                    sortable=field_def.get("sortable", False)
                )
            elif field_def["type"] == "NUMERIC":
                field = NumericField(
                    field_def["name"],
                    sortable=field_def.get("sortable", False)
                )
            elif field_def["type"] == "VECTOR":
                field = VectorField(
                    field_def["name"],
                    field_def["algorithm"],
                    {
                        "TYPE": field_def.get("datatype", "FLOAT32"),
                        "DIM": field_def["dims"],
                        "DISTANCE_METRIC": field_def["distance_metric"]
                    }
                )

            fields.append(field)

        # Create index
        await self.search.create_index(
            fields,
            definition=redis.search.IndexDefinition(
                prefix=[prefix],
                index_type=redis.search.IndexType.JSON
            )
        )

    async def search_text(
        self,
        index_name: str,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        offset: int = 0
    ) -> list[dict]:
        """Perform full-text search with optional filters."""

        # Build query string
        query_str = query
        if filters:
            filter_parts = []
            for field, value in filters.items():
                if isinstance(value, list):
                    filter_parts.append(f"@{field}:({' | '.join(value)})")
                else:
                    filter_parts.append(f"@{field}:{value}")

            if filter_parts:
                query_str = f"({query}) {' '.join(filter_parts)}"

        # Execute search
        q = Query(query_str).paging(offset, limit)
        results = await self.search.search(q, index_name=index_name)

        # Convert results to dicts
        documents = []
        for doc in results.docs:
            doc_dict = {}
            for key, value in doc.__dict__.items():
                if not key.startswith('_'):
                    doc_dict[key] = value
            documents.append(doc_dict)

        return documents

    async def search_vector(
        self,
        index_name: str,
        vector: list[float],
        vector_field: str,
        limit: int = 10,
        threshold: float | None = None
    ) -> list[dict]:
        """Perform vector similarity search."""

        # Build vector query
        vector_str = ','.join(map(str, vector))
        query_str = f"*=>[KNN {limit} @{vector_field} ${vector_field}_vec]"

        q = Query(query_str).return_fields(vector_field, "score").dialect(2)
        q.add_param(f"{vector_field}_vec", vector_str)

        if threshold:
            q = q.add_filter(f"score <= {threshold}")

        results = await self.search.search(q, index_name=index_name)

        # Convert and filter results
        documents = []
        for doc in results.docs:
            if threshold and float(doc.score) > threshold:
                continue

            doc_dict = {}
            for key, value in doc.__dict__.items():
                if not key.startswith('_') and key != 'score':
                    doc_dict[key] = value
            documents.append(doc_dict)

        return documents

    async def save_document(self, key: str, document: dict) -> None:
        """Save document as JSON to Redis."""
        await self.redis.json().set(key, "$", document)

    async def get_document(self, key: str) -> dict | None:
        """Retrieve document by key."""
        result = await self.redis.json().get(key)
        return result

    async def delete_document(self, key: str) -> None:
        """Delete document from Redis."""
        await self.redis.delete(key)
```

## 4. Query Builder System

### 4.1 Query Builder Interface

Create a query builder for complex searches:

```python
# src/enrichmcp/redis/query_builder.py

from typing import Any, Optional
from dataclasses import dataclass

@dataclass
class SearchQuery:
    """Represents a Redis search query."""
    text: Optional[str] = None
    filters: dict[str, Any] | None = None
    vector: Optional[list[float]] = None
    vector_field: Optional[str] = None
    limit: int = 10
    offset: int = 0
    sort_by: Optional[str] = None
    sort_desc: bool = False

class QueryBuilder:
    """Builder for constructing Redis search queries."""

    def __init__(self):
        self.query = SearchQuery()

    def text(self, query: str) -> "QueryBuilder":
        """Add text search query."""
        self.query.text = query
        return self

    def filter(self, field: str, value: Any) -> "QueryBuilder":
        """Add filter condition."""
        if self.query.filters is None:
            self.query.filters = {}
        self.query.filters[field] = value
        return self

    def vector_search(self, vector: list[float], field: str) -> "QueryBuilder":
        """Add vector similarity search."""
        self.query.vector = vector
        self.query.vector_field = field
        return self

    def limit(self, limit: int) -> "QueryBuilder":
        """Set result limit."""
        self.query.limit = limit
        return self

    def offset(self, offset: int) -> "QueryBuilder":
        """Set result offset."""
        self.query.offset = offset
        return self

    def sort(self, field: str, desc: bool = False) -> "QueryBuilder":
        """Add sorting."""
        self.query.sort_by = field
        self.query.sort_desc = desc
        return self

    def build(self) -> SearchQuery:
        """Build the final query."""
        return self.query
```

## 5. Integration with EnrichMCP App

### 5.1 App Extensions

Extend the main EnrichMCP app to support Redis models:

```python
# src/enrichmcp/redis/app_extensions.py

from enrichmcp import EnrichMCP
from .model import RedisModel
from .interface import RedisInterface
from .redis_impl import RedisSearchInterface

class RedisEnrichMCP(EnrichMCP):
    """EnrichMCP with Redis search capabilities."""

    def __init__(
        self,
        title: str,
        instructions: str,
        redis_url: str = "redis://localhost:6379",
        **kwargs
    ):
        super().__init__(title, instructions, **kwargs)
        self.redis_interface = RedisSearchInterface(redis_url)
        self._redis_models: set[type[RedisModel]] = set()

    def redis_entity(self, description: str | None = None):
        """Decorator for Redis-enabled entities."""
        def decorator(cls: type[RedisModel]) -> type[RedisModel]:
            # Register as regular entity first
            self.entity(description)(cls)

            # Track as Redis model
            self._redis_models.add(cls)

            # Set Redis interface
            cls.set_redis_interface(self.redis_interface)

            return cls

        return decorator

    async def initialize_redis_indices(self) -> None:
        """Create all Redis search indices."""
        for model_class in self._redis_models:
            await model_class.create_redis_index()
            await self._create_search_resources(model_class)

    async def run(self, **kwargs) -> None:
        """Run the app with Redis initialization."""
        # Initialize Redis indices before starting
        await self.initialize_redis_indices()

        # Run the regular app
        await super().run(**kwargs)
```

## 6. Usage Examples

### 6.1 Basic Usage

```python
from enrichmcp.redis import RedisEnrichMCP, RedisModel, RedisField

app = RedisEnrichMCP(
    title="Document Search API",
    instructions="Search documents with Redis",
    redis_url="redis://localhost:6379"
)

@app.redis_entity
class Document(RedisModel):
    """A searchable document."""

    # Class-level key template
    __redis_key__ = "doc:{id}"

    id: str = RedisField(description="Document ID", key_component=True)

    title: str = RedisField(
        description="Document title",
        search_type="text",
        weight=2.0,
        searchable=True
    )

    content: str = RedisField(
        description="Document content",
        search_type="text",
        weight=1.0,
        searchable=True
    )

    category: str = RedisField(
        description="Document category",
        search_type="tag",
        filterable=True
    )

    embedding: list[float] = RedisField(
        description="Content embedding",
        search_type="vector",
        dims=1536,
        algorithm="hnsw"
    )

# Auto-generated resources:
# - search_document_by_text(query: str) -> list[Document]
# - filter_document_by_category(category: str) -> list[Document]
# - find_similar_document(vector: list[float]) -> list[Document]
```

### 6.2 Advanced Usage

```python
@app.redis_entity
class Article(RedisModel):
    """A news article with rich search capabilities."""

    # Class-level key template
    __redis_key__ = "article:{id}"

    id: str = RedisField(description="Article ID", key_component=True)

    # Multi-weighted text search
    headline: str = RedisField(
        description="Article headline",
        search_type="text",
        weight=3.0,
        searchable=True
    )

    lead: str = RedisField(
        description="Lead paragraph",
        search_type="text",
        weight=2.0,
        searchable=True
    )

    body: str = RedisField(
        description="Article body",
        search_type="text",
        weight=1.0,
        searchable=True
    )

    # Filterable metadata
    source: str = RedisField(
        description="News source",
        search_type="tag",
        filterable=True
    )

    topics: list[str] = RedisField(
        description="Article topics",
        search_type="tag",
        filterable=True
    )

    # Sortable numeric fields
    published_timestamp: int = RedisField(
        description="Publication timestamp",
        search_type="numeric",
        sortable=True
    )

    # Vector similarity
    content_embedding: list[float] = RedisField(
        description="Semantic embedding",
        search_type="vector",
        dims=1536,
        algorithm="hnsw",
        distance_metric="cosine"
    )
```

## 7. Migration Strategy

### 7.1 Backward Compatibility

1. **Existing EnrichModel**: Continue to work unchanged
2. **Gradual Migration**: Convert models to RedisModel one at a time
3. **Field Enhancement**: Add search metadata to existing fields incrementally
4. **Optional Redis**: Redis features only activate when RedisModel is used

### 7.2 Migration Steps

1. **Phase 1**: Implement RedisField and RedisModel alongside existing system
2. **Phase 2**: Create Redis interface and basic search operations
3. **Phase 3**: Add auto-generated search resources
4. **Phase 4**: Implement advanced features (vector search, complex queries)
5. **Phase 5**: Performance optimization and production hardening

## 8. Testing Strategy

### 8.1 Unit Tests

- Field metadata extraction and validation
- Schema generation from field definitions
- Query building and execution
- Model serialization/deserialization

### 8.2 Integration Tests

- Redis index creation and management
- Search operations across different field types
- Auto-generated resource functionality
- Backward compatibility with existing EnrichMCP features

### 8.3 Performance Tests

- Search performance with large datasets
- Index creation and update performance
- Memory usage and connection management
- Concurrent search operations

## 9. Documentation Requirements

### 9.1 User Documentation

- Migration guide from EnrichModel to RedisModel
- Field type reference with all search options
- Search query examples and best practices
- Performance tuning guidelines

### 9.2 API Documentation

- RedisField parameter reference
- RedisModel method documentation
- Auto-generated resource specifications
- Redis interface abstractions

## 10. Future Enhancements

### 10.1 Advanced Features

- **Faceted Search**: Automatic facet generation from tag fields
- **Aggregations**: Count, sum, average operations on search results
- **Highlighting**: Search term highlighting in results
- **Suggestions**: Auto-complete and spell correction
- **Geospatial**: Location-based search capabilities

### 10.2 Performance Optimizations

- **Connection Pooling**: Efficient Redis connection management
- **Caching**: Query result caching strategies
- **Batch Operations**: Bulk indexing and updates
- **Sharding**: Multi-Redis instance support

This implementation plan provides a comprehensive roadmap for integrating Redis search capabilities into EnrichMCP while maintaining the framework's core principles of simplicity, type safety, and automatic resource generation.
