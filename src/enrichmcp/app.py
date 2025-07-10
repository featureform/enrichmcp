"""
Main application module for enrichmcp.

Provides the EnrichMCP class for creating MCP applications.
"""

import inspect
import warnings
from collections.abc import Callable
from typing import (
    Any,
    Literal,
    Protocol,
    TypeVar,
    cast,
    get_args,
    get_origin,
    runtime_checkable,
)
from uuid import uuid4

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, create_model

from .cache import CacheBackend, ContextCache, MemoryCache
from .context import EnrichContext
from .datamodel import (
    DataModelSummary,
    EntityDescription,
    FieldDescription,
    ModelDescription,
    RelationshipDescription,
)
from .entity import EnrichModel
from .parameter import EnrichParameter
from .relationship import Relationship
from .tool import ToolDef, ToolKind

# Type variables
T = TypeVar("T", bound=EnrichModel)
F = TypeVar("F", bound=Callable[..., Any])


@runtime_checkable
class DecoratorCallable(Protocol):
    """Protocol for decorator callables."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


class EnrichMCP:
    """
    Main application class for enrichmcp.

    This class serves as the entry point for creating MCP applications
    with entity support.
    """

    def __init__(
        self,
        title: str,
        description: str,
        *,
        lifespan: Any = None,
        cache_backend: CacheBackend | None = None,
    ):
        """
        Initialize the EnrichMCP application.

        Args:
            title: API title shown in documentation
            description: Description of the API
            lifespan: Optional async context manager for startup/shutdown lifecycle
        """
        self.title = title
        self.description = description
        self._cache_id = uuid4().hex[:8]
        self.cache_backend = cache_backend or MemoryCache()
        self.mcp = FastMCP(title, description=description, lifespan=lifespan)
        self.name = title  # Required for mcp install

        # Registries
        self.entities: dict[str, type[EnrichModel]] = {}
        self.resolvers: dict[tuple[str, str], dict[str, Any]] = {}
        self.relationships: dict[str, set[Relationship]] = {}
        self.resources: dict[str, Callable[..., Any]] = {}

        # Register built-in resources
        self._register_builtin_resources()

    def data_model_tool_name(self) -> str:
        """Return the name of the built-in data model exploration tool."""

        return f"explore_{self.name.lower().replace(' ', '_')}_data_model"

    def _register_builtin_resources(self) -> None:
        """
        Register built-in resources for the API.
        """

        tool_name = self.data_model_tool_name()
        tool_description = (
            "IMPORTANT: Call this tool at the start of an agent session before"
            f" using other tools on the {self.title} server. {self.description} "
            "This provides a comprehensive overview of the API structure, including"
            " all entities, their fields, relationships, and semantic meanings. "
            "You don't need to call it again if its response is already in context."
        )

        @self.retrieve(name=tool_name, description=tool_description)
        async def explore_data_model() -> "DataModelSummary":  # pyright: ignore[reportUnusedFunction]
            """Return a summary of the API data model."""
            model_description = self.describe_model()
            return DataModelSummary(
                title=self.title,
                description=self.description,
                entity_count=len(self.entities),
                entities=list(self.entities.keys()),
                model=model_description,
                usage_hint=(
                    "Use the model information above to understand how to query the data. "
                    "Each entity has fields and relationships. Relationships must be resolved "
                    "separately using their specific resolver endpoints."
                ),
            )

    def entity(
        self, cls: type[EnrichModel] | None = None, *, description: str | None = None
    ) -> DecoratorCallable:
        """
        Register a model class as an entity.

        This can be used as a decorator with or without arguments:

        @app.entity  # Uses class docstring as description
        class User(EnrichModel):
            \"\"\"User entity for managing user data.\"\"\"
            ...

        @app.entity(description="User entity for managing user data")
        class User(EnrichModel):
            ...

        Args:
            cls: The model class to register
            description: Description of the entity (required unless class has docstring)

        Returns:
            The registered model class

        Raises:
            ValueError: If neither description nor class docstring is provided
        """

        def decorator(cls: type[EnrichModel]) -> type[EnrichModel]:
            # Type hint already ensures this is an EnrichModel subclass

            # Check for description
            if not description and not cls.__doc__:
                raise ValueError(
                    f"Entity '{cls.__name__}' must have a description. "
                    f"Provide it via @app.entity(description=...) or class docstring."
                )

            # Store the description if provided
            if description:
                cls.__doc__ = description

            # Check that all fields have descriptions
            for field_name, field in cls.model_fields.items():
                # Skip relationship fields which are validated separately
                if field_name in cls.relationship_fields():
                    continue

                # Check if the field has a description
                if not field.description:
                    raise ValueError(
                        f"Field '{field_name}' in entity '{cls.__name__}' must have a description. "
                        f"Use Field(..., description=...) to provide one."
                    )

            # Register the entity
            self.entities[cls.__name__] = cls

            # Store a reference to the app in the class
            cls._app = self  # pyright: ignore[reportAttributeAccessIssue]

            # Add relationship fields as class attributes
            for field_name, field in cls.model_fields.items():
                if isinstance(field.default, Relationship):
                    relationship = field.default
                    relationship.app = self
                    relationship.field_name = field_name
                    relationship.owner_cls = cls

                    # Add the relationship as a class attribute
                    setattr(cls, field_name, relationship)

            # Find and register relationships
            self._register_relationships(cls)

            # Generate PatchModel for mutable fields
            self._generate_patch_model(cls)

            return cls

        return decorator(cls) if cls else decorator

    def _register_relationships(self, cls: type[EnrichModel]) -> None:
        """
        Register relationships for an entity class.

        Args:
            cls: The entity class to process
        """
        self.relationships[cls.__name__] = cls.relationships()

    def _generate_patch_model(self, cls: type[EnrichModel]) -> None:
        """Create an auto-generated PatchModel on the entity class."""
        mutable_fields = {}
        for name, field in cls.model_fields.items():
            extra = getattr(field, "json_schema_extra", None)
            if extra is None:
                info = getattr(field, "field_info", None)
                extra = getattr(info, "extra", {}) if info is not None else {}
            if extra.get("mutable") is True and name not in cls.relationship_fields():
                annotation = field.annotation or Any
                mutable_fields[name] = (
                    annotation | None,
                    Field(
                        default=None,
                        description=field.description,
                    ),
                )

        if mutable_fields:
            patch_model_cls = create_model(
                f"{cls.__name__}PatchModel",
                __base__=BaseModel,
                **mutable_fields,
            )
            patch_model_cls.__doc__ = f"Patch model for {cls.__name__}"
            cls.PatchModel = patch_model_cls

    def describe_model_struct(self) -> ModelDescription:
        """Return a structured description of the entire data model."""
        desc = ModelDescription(title=self.title, description=self.description)

        for entity_name, entity_cls in sorted(self.entities.items()):
            entity_desc = EntityDescription(
                name=entity_name,
                description=(entity_cls.__doc__ or "No description available").strip(),
            )

            for field_name, field in entity_cls.model_fields.items():
                if field_name in entity_cls.relationship_fields():
                    continue

                field_type = "Any"
                if field.annotation is not None:
                    annotation = field.annotation
                    if get_origin(annotation) is Literal:
                        values = ", ".join(repr(v) for v in get_args(annotation))
                        field_type = f"Literal[{values}]"
                    else:
                        field_type = str(annotation)
                        if hasattr(annotation, "__name__"):
                            field_type = annotation.__name__

                extra = getattr(field, "json_schema_extra", None)
                if extra is None:
                    info = getattr(field, "field_info", None)
                    extra = getattr(info, "extra", {}) if info is not None else {}

                entity_desc.fields.append(
                    FieldDescription(
                        name=field_name,
                        type=field_type,
                        description=field.description or "",
                        mutable=bool(extra.get("mutable")),
                    )
                )

            for field_name in entity_cls.relationship_fields():
                field = entity_cls.model_fields[field_name]
                rel = field.default
                target_type = "Any"
                if field.annotation is not None:
                    target_type = str(field.annotation)
                    if hasattr(field.annotation, "__name__"):
                        target_type = field.annotation.__name__

                entity_desc.relationships.append(
                    RelationshipDescription(
                        name=field_name,
                        target=target_type,
                        description=rel.description,
                    )
                )

            desc.entities.append(entity_desc)

        return desc

    def describe_model(self) -> str:
        """Return a Markdown description of the entire data model."""
        return str(self.describe_model_struct())

    def _append_enrichparameter_hints(self, description: str, fn: Callable[..., Any]) -> str:
        """Append ``EnrichParameter`` metadata to a description string."""

        hints: list[str] = []
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):  # pragma: no cover - defensive
            return description

        for param in sig.parameters.values():
            default = param.default
            annotation = param.annotation

            if isinstance(default, EnrichParameter):
                if annotation is EnrichContext:
                    # Context parameters are stripped from the final tool
                    # interface so hints would be confusing to the agent.
                    continue

                param_type = "Any"
                if annotation is not inspect.Parameter.empty:
                    if get_origin(annotation) is Literal:
                        values = ", ".join(repr(v) for v in get_args(annotation))
                        param_type = f"Literal[{values}]"
                    else:
                        param_type = getattr(annotation, "__name__", str(annotation))

                parts = [param_type]
                if default.description:
                    parts.append(default.description)
                if default.examples:
                    joined = ", ".join(map(str, default.examples))
                    parts.append(f"examples: {joined}")
                if default.metadata:
                    meta = ", ".join(f"{k}: {v}" for k, v in default.metadata.items())
                    parts.append(meta)

                hints.append(f"{param.name} - {'; '.join(parts)}")

        if hints:
            description = (
                description.rstrip() + "\n\nParameter hints:\n" + "\n".join(f"- {h}" for h in hints)
            )

        return description

    def _register_tool_def(self, fn: Callable[..., Any], tool_def: ToolDef) -> Callable[..., Any]:
        """Register ``fn`` as a tool using ``tool_def``."""

        desc = self._append_enrichparameter_hints(tool_def.final_description(self), fn)
        self.resources[tool_def.name] = fn
        mcp_tool = self.mcp.tool(name=tool_def.name, description=desc)
        return mcp_tool(fn)

    def _tool_decorator(
        self,
        kind: ToolKind,
        func: Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Callable[..., Any] | DecoratorCallable:
        """Return a decorator that registers a tool of the given ``kind``."""

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            tool_name = name or fn.__name__
            tool_desc = description or fn.__doc__
            if not tool_desc:
                raise ValueError(
                    f"Resource '{tool_name}' must have a description. "
                    "Provide it via the decorator or function docstring."
                )

            if tool_desc == fn.__doc__ and tool_desc:
                tool_desc = tool_desc.strip()

            tool_def = ToolDef(kind=kind, name=tool_name, description=tool_desc)
            return self._register_tool_def(fn, tool_def)

        if func is not None:
            return decorator(func)

        return cast("DecoratorCallable", decorator)

    def retrieve(
        self,
        func: Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Callable[..., Any] | DecoratorCallable:
        """
        Register a function as an MCP resource.

        Can be used as:
            @app.retrieve
            async def my_resource():
                '''Resource description in docstring'''
                ...

        Or with explicit parameters:
            @app.retrieve(name="custom_name", description="Custom description")
            async def my_resource():
                ...

        Args:
            func: The function to register (when used without parentheses)
            name: Override function name (default: function.__name__)
            description: Override description (default: function.__doc__)

        Returns:
            Decorated function or decorator

        Raises:
            ValueError: If no description is provided (neither in decorator nor docstring)
        """

        return self._tool_decorator(ToolKind.RETRIEVER, func, name=name, description=description)

    def resource(self, *args: Any, **kwargs: Any) -> Any:
        """Deprecated alias for :meth:`retrieve`. Use :meth:`retrieve` instead."""
        warnings.warn(
            "app.resource is deprecated; use app.retrieve instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.retrieve(*args, **kwargs)

    # CRUD helper decorators
    def create(
        self,
        func: Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Callable[..., Any] | DecoratorCallable:
        """Register a create operation."""

        return self._tool_decorator(ToolKind.CREATOR, func, name=name, description=description)

    def update(
        self,
        func: Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Callable[..., Any] | DecoratorCallable:
        """Register an update operation."""

        return self._tool_decorator(ToolKind.UPDATER, func, name=name, description=description)

    def delete(
        self,
        func: Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Callable[..., Any] | DecoratorCallable:
        """Register a delete operation."""

        return self._tool_decorator(ToolKind.DELETER, func, name=name, description=description)

    def get_context(self) -> EnrichContext:
        """Return the current :class:`EnrichContext` for this app."""

        base_ctx = self.mcp.get_context()
        request_ctx = getattr(base_ctx, "_request_context", None)
        rid = str(getattr(request_ctx, "request_id", "")) if request_ctx else ""
        request_id = rid if rid else uuid4().hex
        ctx = EnrichContext.model_construct(
            _request_context=request_ctx,
            _fastmcp=getattr(base_ctx, "_fastmcp", None),
        )
        ctx._cache = ContextCache(self.cache_backend, self._cache_id, request_id)
        return ctx

    def run(
        self, *, transport: str | None = None, mount_path: str | None = None, **options: Any
    ) -> Any:
        """
        Start the MCP server.

        Args:
            transport: Transport protocol to use when starting the server.
                Supported values are "stdio", "sse", and "streamable-http".
                If not provided, the default from ``FastMCP`` is used.
            mount_path: Optional mount path for SSE transport.
            **options: Additional options forwarded to ``FastMCP.run``.

        Returns:
            Result from FastMCP.run()

        Raises:
            ValueError: If any relationships are missing resolvers
        """
        # Check that all relationships have resolvers
        unresolved: list[str] = []
        for entity_name, entity_cls in self.entities.items():
            for field_name, field in entity_cls.model_fields.items():
                if field_name in entity_cls.relationship_fields():
                    relationship = field.default
                    if not relationship.is_resolved():
                        unresolved.append(f"{entity_name}.{field_name}")

        if unresolved:
            raise ValueError(
                f"The following relationships are missing resolvers: {', '.join(unresolved)}. "
                f"Define resolvers with @Entity.relationship.resolver"
            )

        # Forward transport options to FastMCP
        if transport is not None:
            options.setdefault("transport", transport)
        if mount_path is not None:
            options.setdefault("mount_path", mount_path)

        # Run the MCP server
        return self.mcp.run(**options)
