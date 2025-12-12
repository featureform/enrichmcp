"""Redis backend implementation for search operations."""

from typing import Any

import redis.asyncio as redis
from redis.commands.search.field import NumericField, TagField, TextField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query


class RedisBackend:
    """Redis backend for search operations using redis-py."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize Redis backend.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.client: redis.Redis | None = None

    async def connect(self):
        """Connect to Redis."""
        if self.client is None:
            self.client = redis.from_url(self.redis_url, decode_responses=True)
            await self.client.ping()  # Test connection

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
            self.client = None

    async def create_index(
        self, index_name: str, prefix: str, fields: list[dict[str, Any]]
    ) -> None:
        """Create Redis search index.

        Args:
            index_name: Name of the index to create
            prefix: Key prefix for documents (e.g., "user:")
            fields: List of field definitions with Redis metadata
        """
        await self.connect()

        # Convert field definitions to redis-py field objects
        redis_fields = []

        for field_def in fields:
            field_name = field_def["name"]
            field_type = field_def["type"]

            if field_type == "text":
                field = TextField(
                    f"$.{field_name}",
                    as_name=field_name,
                    weight=field_def.get("weight", 1.0),
                    no_stem=field_def.get("no_stem", False),
                )
            elif field_type == "tag":
                field = TagField(f"$.{field_name}", as_name=field_name)
            elif field_type == "numeric":
                field = NumericField(
                    f"$.{field_name}", as_name=field_name, sortable=field_def.get("sortable", False)
                )
            elif field_type == "vector":
                field = VectorField(
                    f"$.{field_name}",
                    "HNSW",  # Default to HNSW algorithm
                    {
                        "TYPE": "FLOAT32",
                        "DIM": field_def["vector_dim"],
                        "DISTANCE_METRIC": field_def.get("distance_metric", "COSINE").upper(),
                    },
                    as_name=field_name,
                )
            else:
                continue  # Skip unknown field types

            redis_fields.append(field)

        if not redis_fields:
            return  # No searchable fields

        # Create index definition
        definition = IndexDefinition(prefix=[prefix], index_type=IndexType.JSON)

        try:
            if self.client:
                await self.client.ft(index_name).create_index(
                    fields=redis_fields, definition=definition
                )
        except Exception as e:
            if "Index already exists" not in str(e):
                raise

    async def save_document(self, key: str, doc: dict[str, Any]) -> None:
        """Save document to Redis.

        Args:
            key: Redis key for the document
            doc: Document data to store
        """
        await self.connect()
        if self.client is not None:
            await self.client.json().set(key, "$", doc)  # type: ignore[misc]

    async def get_document(self, key: str) -> dict[str, Any] | None:
        """Get document from Redis.

        Args:
            key: Redis key for the document

        Returns:
            Document data or None if not found
        """
        await self.connect()
        if self.client is None:
            return None
        try:
            result = await self.client.json().get(key)  # type: ignore[misc]
            return result  # type: ignore[return-value]
        except Exception:
            return None

    async def search_text(
        self, index: str, query: str, limit: int = 10, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Execute text search query.

        Args:
            index: Index name to search
            query: Search query string
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of matching documents
        """
        await self.connect()
        if not self.client:
            return []

        q = Query(query).paging(offset, limit)
        try:
            results = await self.client.ft(index).search(q)
            docs = []
            for doc in results.docs:
                doc_dict = self._doc_to_dict(doc)
                if doc_dict:  # Only add non-empty documents
                    docs.append(doc_dict)
            return docs
        except Exception as e:
            print(f"Redis search error: {e}")
            return []

    async def search_by_field(
        self, index: str, field: str, value: str, limit: int = 10, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Search by specific field value.

        Args:
            index: Index name to search
            field: Field name to search
            value: Value to search for
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of matching documents
        """
        await self.connect()
        if not self.client:
            return []

        # Escape special characters in value for tag queries
        escaped_value = value.replace(":", "\\:")

        # Tag fields require curly braces syntax: @field:{value}
        q = Query(f"@{field}:{{{escaped_value}}}").paging(offset, limit)

        try:
            results = await self.client.ft(index).search(q)
            docs = []
            for doc in results.docs:
                doc_dict = self._doc_to_dict(doc)
                if doc_dict:  # Only add non-empty documents
                    docs.append(doc_dict)
            return docs
        except Exception as e:
            print(f"Redis field search error: {e}")
            return []

    async def search_numeric_range(
        self,
        index: str,
        field: str,
        min_val: float,
        max_val: float,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Search by numeric range.

        Args:
            index: Index name to search
            field: Numeric field name
            min_val: Minimum value (inclusive)
            max_val: Maximum value (inclusive)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of matching documents
        """
        await self.connect()
        if not self.client:
            return []

        q = Query(f"@{field}:[{min_val} {max_val}]").paging(offset, limit)

        try:
            results = await self.client.ft(index).search(q)
            docs = []
            for doc in results.docs:
                doc_dict = self._doc_to_dict(doc)
                if doc_dict:  # Only add non-empty documents
                    docs.append(doc_dict)
            return docs
        except Exception as e:
            print(f"Redis numeric range search error: {e}")
            return []

    def _doc_to_dict(self, doc) -> dict[str, Any]:
        """Convert Redis document to dictionary.

        Args:
            doc: Redis search result document

        Returns:
            Document as dictionary
        """
        try:
            # Handle different document formats
            if hasattr(doc, "json"):
                # JSON document - return the JSON content
                json_data = doc.json
                # Handle case where json is a string that needs parsing
                if isinstance(json_data, str):
                    import json

                    try:
                        return json.loads(json_data)
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}, data: {json_data}")
                        return {}
                elif isinstance(json_data, dict):
                    return json_data
                else:
                    print(f"Unexpected json data type: {type(json_data)}, value: {json_data}")
                    return {}
            elif hasattr(doc, "__dict__"):
                # Regular document - extract fields
                result = {}
                for key, value in doc.__dict__.items():
                    if not key.startswith("_"):
                        result[key] = value
                return result
            else:
                # Fallback - return as-is if it's already a dict
                if isinstance(doc, dict):
                    return doc
                else:
                    print(f"Unknown document type: {type(doc)}, value: {doc}")
                    return {}
        except Exception as e:
            print(f"Error converting document to dict: {e}, doc: {doc}")
            return {}
