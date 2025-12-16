"""Enhanced EnrichModel with Redis capabilities."""

from typing import Any

from enrichmcp import EnrichModel as BaseEnrichModel


class EnrichModel(BaseEnrichModel):
    """Enhanced EnrichModel with Redis search capabilities."""

    @classmethod
    def get_redis_fields(cls) -> list[dict[str, Any]]:
        """Extract Redis search fields from model metadata.

        Returns:
            List of field definitions with Redis search metadata
        """
        fields = []

        for field_name, field_info in cls.model_fields.items():
            # Skip relationship fields - check if this is a Relationship descriptor
            if hasattr(cls, field_name):
                attr = getattr(cls, field_name)
                if hasattr(attr, "__class__") and "Relationship" in str(attr.__class__):
                    continue

            # Check for Redis metadata in the field
            redis_meta = None
            if hasattr(field_info, "json_schema_extra") and field_info.json_schema_extra:
                redis_meta = field_info.json_schema_extra.get("redis_search")

            if (
                redis_meta
                and isinstance(redis_meta, dict)
                and redis_meta.get("index")
                and isinstance(redis_meta["index"], list)
            ):
                for index_type in redis_meta["index"]:
                    field_def = {
                        "name": field_name,
                        "type": index_type,
                        "description": field_info.description or "",
                    }

                    # Add type-specific metadata
                    if index_type == "vector":
                        field_def.update(
                            {
                                "vector_dim": redis_meta.get("vector_dim"),
                                "distance_metric": redis_meta.get("distance_metric", "cosine"),
                            }
                        )
                    elif index_type == "text":
                        field_def.update(
                            {
                                "weight": redis_meta.get("weight", 1.0),
                                "no_stem": redis_meta.get("no_stem", False),
                            }
                        )
                    elif index_type == "numeric":
                        field_def.update(
                            {
                                "sortable": redis_meta.get("sortable", False),
                            }
                        )

                    fields.append(field_def)

        return fields

    @classmethod
    def get_redis_key_prefix(cls) -> str:
        """Get Redis key prefix for this model.

        Returns:
            Key prefix like "user:" or "product:"
        """
        return f"{cls.__name__.lower()}:"

    @classmethod
    def get_redis_index_name(cls) -> str:
        """Get Redis index name for this model.

        Returns:
            Index name like "user_idx" or "product_idx"
        """
        return f"{cls.__name__.lower()}_idx"

    def redis_key(self) -> str:
        """Generate Redis key for this instance.

        Returns:
            Redis key like "user:123" or "product:456"
        """
        return f"{self.get_redis_key_prefix()}{self.id}"

    def redis_document(self) -> dict[str, Any]:
        """Convert to Redis document (exclude relationships, handle field types).

        Returns:
            Dictionary suitable for Redis JSON storage with proper field type conversion
        """
        # Use mode="json" to ensure datetime objects are serialized as ISO strings
        doc = self.model_dump(mode="json")

        # Remove relationship fields - check for Relationship descriptors
        for field_name in list(doc.keys()):
            if hasattr(self.__class__, field_name):
                attr = getattr(self.__class__, field_name)
                if hasattr(attr, "__class__") and "Relationship" in str(attr.__class__):
                    doc.pop(field_name, None)

        # Convert field types for Redis indexing compatibility
        redis_fields = self.get_redis_fields()
        for field_def in redis_fields:
            field_name = field_def["name"]
            field_type = field_def["type"]

            if field_name in doc and field_type == "tag":
                # TAG fields require string values, convert integers to strings
                value = doc[field_name]
                if isinstance(value, int | float) or (
                    value is not None and not isinstance(value, str)
                ):
                    doc[field_name] = str(value)

        return doc
