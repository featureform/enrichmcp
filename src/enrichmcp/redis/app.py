"""Redis-enabled EnrichMCP application."""

from typing import Any

from enrichmcp import EnrichMCP as BaseEnrichMCP

from .backend import RedisBackend
from .model import EnrichModel


class EnrichMCP(BaseEnrichMCP):
    """Redis-enabled EnrichMCP application.

    Extends the base EnrichMCP with Redis search capabilities including
    automatic index creation, document storage, and MCP resource generation.
    """

    def __init__(
        self, title: str, instructions: str, redis_url: str = "redis://localhost:6379", **kwargs
    ):
        """Initialize Redis-enabled EnrichMCP app.

        Args:
            title: Application title
            instructions: Application instructions
            redis_url: Redis connection URL
            **kwargs: Additional arguments passed to base EnrichMCP
        """
        super().__init__(title=title, instructions=instructions, **kwargs)
        self.redis_backend = RedisBackend(redis_url)
        self._redis_models: dict[str, type[EnrichModel]] = {}

    def entity(self, description: str | None = None):
        """Enhanced entity decorator that tracks Redis models.

        Args:
            description: Entity description

        Returns:
            Decorator function
        """

        def decorator(cls: type[EnrichModel]) -> type[EnrichModel]:
            # Register as regular entity with base class
            base_decorator = BaseEnrichMCP.entity(self, description=description)
            decorated_cls = base_decorator(cls)

            # Track for Redis operations if it has Redis fields
            redis_fields = decorated_cls.get_redis_fields()
            if redis_fields:
                model_name = decorated_cls.__name__.lower()
                self._redis_models[model_name] = decorated_cls

            return decorated_cls

        return decorator

    async def apply(self, sample_data: dict[str, list[dict[str, Any]]] | None = None):
        """Create Redis indices and populate sample data.

        Args:
            sample_data: Optional sample data to populate, keyed by model name (plural)
        """
        print("🔧 Setting up Redis indices and data...")

        # 1. Create indices for all registered models
        for model_name, model_class in self._redis_models.items():
            await self._create_model_index(model_name, model_class)

        # 2. Populate sample data if provided
        if sample_data:
            await self._populate_sample_data(sample_data)

        # 3. Auto-generate MCP resources
        for model_name, model_class in self._redis_models.items():
            await self._generate_search_resources(model_name, model_class)

        # 4. Auto-generate relationship resolvers
        await self._generate_relationship_resolvers()

        print("✅ Redis setup complete!")

    async def _create_model_index(self, model_name: str, model_class: type[EnrichModel]):
        """Create Redis index for a model.

        Args:
            model_name: Name of the model (lowercase)
            model_class: Model class
        """
        redis_fields = model_class.get_redis_fields()
        if not redis_fields:
            return

        index_name = model_class.get_redis_index_name()
        key_prefix = model_class.get_redis_key_prefix()

        await self.redis_backend.create_index(index_name, key_prefix, redis_fields)

        # Log created index
        field_summary = {}
        for field in redis_fields:
            field_type = field["type"]
            if field_type not in field_summary:
                field_summary[field_type] = []
            field_summary[field_type].append(field["name"])

        summary_parts = []
        for field_type, field_names in field_summary.items():
            summary_parts.append(f"{field_type}: {','.join(field_names)}")

        print(f"📊 Created {index_name} ({' | '.join(summary_parts)})")

    async def _populate_sample_data(self, sample_data: dict[str, list[dict[str, Any]]]):
        """Populate Redis with sample data.

        Args:
            sample_data: Sample data keyed by model name (plural)
        """
        for data_key, items in sample_data.items():
            # Convert plural key to model name (simple approach)
            model_name = data_key.rstrip("s")  # users -> user, products -> product

            if model_name in self._redis_models:
                model_class = self._redis_models[model_name]

                for item_data in items:
                    # Create model instance to get proper key
                    instance = model_class(**item_data)
                    redis_key = instance.redis_key()
                    redis_doc = instance.redis_document()

                    await self.redis_backend.save_document(redis_key, redis_doc)

                print(f"💾 Populated {len(items)} {data_key}")

    async def _generate_search_resources(self, model_name: str, model_class: type[EnrichModel]):
        """Auto-generate MCP resources for search operations.

        Args:
            model_name: Name of the model (lowercase)
            model_class: Model class
        """
        redis_fields = model_class.get_redis_fields()
        index_name = model_class.get_redis_index_name()

        # Group fields by type
        text_fields = [f for f in redis_fields if f["type"] == "text"]
        tag_fields = [f for f in redis_fields if f["type"] == "tag"]
        numeric_fields = [f for f in redis_fields if f["type"] == "numeric"]
        primary_fields = [f for f in redis_fields if f["type"] == "primary"]

        # Generate text search resource
        if text_fields:
            await self._create_text_search_resource(model_name, model_class, index_name)

        # Generate tag filter resources
        for field in tag_fields:
            await self._create_tag_filter_resource(model_name, model_class, index_name, field)

        # Generate numeric range resources
        for field in numeric_fields:
            await self._create_numeric_range_resource(model_name, model_class, index_name, field)

        # Generate primary key lookup resource
        if primary_fields:
            await self._create_primary_key_resource(model_name, model_class)

    async def _create_text_search_resource(
        self, model_name: str, model_class: type[EnrichModel], index_name: str
    ):
        """Create text search resource."""
        resource_name = f"search_{model_name}_by_text"

        async def search_text(query: str, limit: int = 10) -> list[Any]:
            """Search by text content."""
            results = await self.redis_backend.search_text(index_name, query, limit)
            models = []
            for doc in results:
                try:
                    if isinstance(doc, dict):
                        models.append(model_class(**doc))
                    else:
                        # Convert Redis document to dict first
                        doc_dict = self.redis_backend._doc_to_dict(doc)
                        if doc_dict:
                            models.append(model_class(**doc_dict))
                except Exception as e:
                    # Skip invalid documents but log the error
                    print(f"Warning: Failed to create {model_class.__name__} from document: {e}")
                    continue
            return models

        search_text.__name__ = resource_name
        self.tool()(search_text)

    async def _create_tag_filter_resource(
        self,
        model_name: str,
        model_class: type[EnrichModel],
        index_name: str,
        field: dict[str, Any],
    ):
        """Create tag filter resource."""
        field_name = field["name"]
        resource_name = f"filter_{model_name}_by_{field_name}"

        async def filter_by_tag(value: str, limit: int = 10) -> list[Any]:
            """Filter by tag field."""
            results = await self.redis_backend.search_by_field(index_name, field_name, value, limit)
            models = []
            for doc in results:
                try:
                    if isinstance(doc, dict):
                        models.append(model_class(**doc))
                    else:
                        # Convert Redis document to dict first
                        doc_dict = self.redis_backend._doc_to_dict(doc)
                        if doc_dict:
                            models.append(model_class(**doc_dict))
                except Exception as e:
                    # Skip invalid documents but log the error
                    print(f"Warning: Failed to create {model_class.__name__} from document: {e}")
                    continue
            return models

        filter_by_tag.__name__ = resource_name
        self.tool()(filter_by_tag)

    async def _create_numeric_range_resource(
        self,
        model_name: str,
        model_class: type[EnrichModel],
        index_name: str,
        field: dict[str, Any],
    ):
        """Create numeric range resource."""
        field_name = field["name"]
        resource_name = f"find_{model_name}_by_{field_name}_range"

        async def find_by_range(min_value: float, max_value: float, limit: int = 10) -> list[Any]:
            """Find by numeric range."""
            results = await self.redis_backend.search_numeric_range(
                index_name, field_name, min_value, max_value, limit
            )
            models = []
            for doc in results:
                try:
                    if isinstance(doc, dict):
                        models.append(model_class(**doc))
                    else:
                        # Convert Redis document to dict first
                        doc_dict = self.redis_backend._doc_to_dict(doc)
                        if doc_dict:
                            models.append(model_class(**doc_dict))
                except Exception as e:
                    # Skip invalid documents but log the error
                    print(f"Warning: Failed to create {model_class.__name__} from document: {e}")
                    continue
            return models

        find_by_range.__name__ = resource_name
        self.tool()(find_by_range)

    async def _create_primary_key_resource(self, model_name: str, model_class: type[EnrichModel]):
        """Create primary key lookup resource."""
        resource_name = f"get_{model_name}_by_id"

        async def get_by_id(id: int) -> Any | None:
            """Get by ID."""
            key = f"{model_class.get_redis_key_prefix()}{id}"
            doc = await self.redis_backend.get_document(key)
            if doc:
                try:
                    if isinstance(doc, dict):
                        return model_class(**doc)
                    else:
                        # Convert Redis document to dict first
                        doc_dict = self.redis_backend._doc_to_dict(doc)
                        if doc_dict:
                            return model_class(**doc_dict)
                except Exception as e:
                    print(f"Warning: Failed to create {model_class.__name__} from document: {e}")
            return None

        get_by_id.__name__ = resource_name
        self.tool()(get_by_id)

    async def _generate_relationship_resolvers(self):
        """Auto-generate relationship resolvers for all registered models."""
        print("🔗 Auto-generating relationship resolvers...")

        # Generate resolvers for each Redis entity
        resolver_count = 0
        for _entity_name, entity_class in self._redis_models.items():
            count = await self._generate_entity_relationship_resolvers(entity_class)
            resolver_count += count

        if resolver_count > 0:
            print(f"   ✓ Generated {resolver_count} relationship resolvers")

    def run(
        self,
        *,
        transport: str | None = None,
        mount_path: str | None = None,
        **options: Any,
    ) -> Any:
        """Start the Redis MCP server with automatic tool generation.

        Args:
            transport: Transport protocol to use when starting the server.
            mount_path: Optional mount path for SSE transport.
            **options: Additional options forwarded to ``FastMCP.run``.

        Returns:
            Result from FastMCP.run()
        """
        import asyncio

        # Auto-generate tools (search resources and relationship resolvers) before starting
        if self._redis_models:
            print("🔧 Auto-generating Redis tools...")

            # Create a new event loop for setup if needed
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're in an async context, we need a new loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    should_close = True
                else:
                    should_close = False
            except RuntimeError:
                # No event loop exists
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                should_close = True

            try:
                # Only generate tools, not sample data
                # 1. Generate search resources for all models
                for model_name, model_class in self._redis_models.items():
                    loop.run_until_complete(
                        self._generate_search_resources(model_name, model_class)
                    )

                # 2. Generate relationship resolvers
                loop.run_until_complete(self._generate_relationship_resolvers())

                print("   ✓ Auto-generated Redis search and relationship tools")
            finally:
                if should_close:
                    loop.close()

        # Call parent run method
        return super().run(transport=transport, mount_path=mount_path, **options)

    async def _generate_entity_relationship_resolvers(self, entity_class: type[Any]) -> int:
        """Generate relationship resolvers for a specific entity.

        Returns:
            Number of resolvers created
        """
        # Get relationship fields from the class metadata
        relationships = getattr(entity_class, "_relationships", {})
        resolver_count = 0

        for field_name, relationship in relationships.items():
            # Check if resolver already exists
            if hasattr(relationship, "resolvers") and relationship.resolvers:
                continue  # Skip if manually defined

            # Auto-generate resolver based on relationship metadata
            success = await self._create_relationship_resolver(
                entity_class, field_name, relationship
            )
            if success:
                resolver_count += 1

        return resolver_count

    async def _create_relationship_resolver(
        self, entity_class: type[Any], field_name: str, relationship
    ) -> bool:
        """Create a relationship resolver based on metadata.

        Returns:
            True if resolver was created successfully
        """
        # Get the target type from the relationship's stored annotation
        if not hasattr(relationship, "target_type") or not relationship.target_type:
            print(f"         No target_type found for {field_name}")
            return False

        annotation = relationship.target_type
        print(f"         Target type: {annotation}")

        # Handle List[TargetModel] vs TargetModel
        is_list = False
        target_class = None

        # Import get_origin and get_args for proper type inspection
        from typing import get_args, get_origin

        # Handle string annotations (forward references)
        if isinstance(annotation, str):
            # Remove quotes if present
            clean_annotation = annotation.strip("'\"")
            # Parse string annotations like "list[Order]" or "Order"
            if clean_annotation.startswith("list[") and clean_annotation.endswith("]"):
                is_list = True
                target_class = clean_annotation[5:-1]  # Extract "Order" from "list[Order]"
            else:
                target_class = clean_annotation
        else:
            # Handle actual type objects
            origin = get_origin(annotation)
            if origin is list:
                is_list = True
                args = get_args(annotation)
                if args:
                    target_class = args[0]
            else:
                target_class = annotation

        # Handle forward references (string class names)
        if isinstance(target_class, str):
            # Look up the class by name in registered entities (try both registries)
            # First try exact match in entities
            if target_class in self.entities:
                target_class = self.entities[target_class]
            # Then try lowercase match in redis_models
            elif target_class.lower() in self._redis_models:
                target_class = self._redis_models[target_class.lower()]
            # Try case-insensitive match in entities
            else:
                found = False
                for entity_name, entity_class in self.entities.items():
                    if entity_name.lower() == target_class.lower():
                        target_class = entity_class
                        found = True
                        break
                if not found:
                    return False

        if not target_class or not hasattr(target_class, "__name__"):
            return False

        # Type guard to ensure target_class is a proper class type
        if isinstance(target_class, str):
            return False

        # Create resolver function
        if hasattr(relationship, "source_field") and relationship.source_field:
            # Forward relationship: use source_field to find related records
            await self._create_forward_resolver(
                entity_class, field_name, relationship, target_class, is_list
            )
            return True
        else:
            # No supported relationship type found
            return False

    async def _create_forward_resolver(
        self,
        entity_class: type[Any],
        field_name: str,
        relationship,
        target_class: type[Any],
        is_list: bool,
    ):
        """Create forward relationship resolver (using source_field)."""
        source_field = relationship.source_field
        target_model_name = target_class.__name__.lower()

        if is_list:
            # One-to-many: source_field contains list of IDs
            async def forward_list_resolver(instance):
                # Handle both dict (from MCP) and model instance
                if isinstance(instance, dict):
                    source_value = instance.get(source_field)
                else:
                    source_value = getattr(instance, source_field, None)

                if not source_value:
                    return []

                # Handle both single ID and list of IDs
                if not isinstance(source_value, list):
                    source_value = [source_value]

                results = []
                for item_id in source_value:
                    key = f"{target_model_name}:{item_id}"
                    doc = await self.redis_backend.get_document(key)
                    if doc:
                        try:
                            if isinstance(doc, dict):
                                results.append(target_class(**doc))
                            else:
                                doc_dict = self.redis_backend._doc_to_dict(doc)
                                if doc_dict:
                                    results.append(target_class(**doc_dict))
                        except Exception as e:
                            print(
                                f"Warning: Failed to create {target_class.__name__} "
                                f"from document: {e}"
                            )
                            continue
                return results

            forward_list_resolver.__name__ = f"resolve_{entity_class.__name__.lower()}_{field_name}"
            # Skip setting return type annotation to avoid forward reference issues
        else:
            # One-to-one: source_field contains single ID
            async def forward_single_resolver(instance):
                # Handle both dict (from MCP) and model instance
                if isinstance(instance, dict):
                    source_value = instance.get(source_field)
                else:
                    source_value = getattr(instance, source_field, None)

                if not source_value:
                    return None

                key = f"{target_model_name}:{source_value}"
                doc = await self.redis_backend.get_document(key)
                if doc:
                    try:
                        if isinstance(doc, dict):
                            return target_class(**doc)
                        else:
                            doc_dict = self.redis_backend._doc_to_dict(doc)
                            if doc_dict:
                                return target_class(**doc_dict)
                    except Exception as e:
                        print(
                            f"Warning: Failed to create {target_class.__name__} from document: {e}"
                        )
                return None

            forward_single_resolver.__name__ = (
                f"resolve_{entity_class.__name__.lower()}_{field_name}"
            )
            # Skip setting return type annotation to avoid forward reference issues

        # Register the resolver
        resolver_func = forward_list_resolver if is_list else forward_single_resolver
        relationship_attr = getattr(entity_class, field_name)
        if hasattr(relationship_attr, "resolver"):
            relationship_attr.resolver(name="get")(resolver_func)
