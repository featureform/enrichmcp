"""
Main application module for enrichmcp.

Provides the EnrichMCP class for creating MCP applications.
"""

from collections.abc import Callable
from typing import (
    Any,
    Protocol,
    TypeVar,
    cast,
    runtime_checkable,
)

from mcp.server.fastmcp import FastMCP

from .entity import EnrichModel
from .relationship import Relationship

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

    def __init__(self, title: str, description: str, *, lifespan: Any = None):
        """
        Initialize the EnrichMCP application.

        Args:
            title: API title shown in documentation
            description: Description of the API
            lifespan: Optional async context manager for startup/shutdown lifecycle
        """
        self.title = title
        self.description = description
        self.mcp = FastMCP(title, description=description, lifespan=lifespan)
        self.name = title  # Required for mcp install

        # Registries
        self.entities: dict[str, type[EnrichModel]] = {}
        self.resolvers: dict[tuple[str, str], dict[str, Any]] = {}
        self.relationships: dict[str, set[Relationship]] = {}
        self.resources: dict[str, Callable[..., Any]] = {}

        # Register built-in resources
        self._register_builtin_resources()

    def _register_builtin_resources(self) -> None:
        """
        Register built-in resources for the API.
        """

        @self.resource(
            name="explore_data_model",
            description=(
                "IMPORTANT: Call this tool FIRST to understand the complete data model, "
                "entity relationships, and available operations. This provides a comprehensive "
                "overview of the API structure, including all entities, their fields, "
                "relationships, and semantic meanings. Understanding this model is essential "
                "for effectively querying and navigating the data."
            ),
        )
        async def explore_data_model() -> dict[str, Any]:  # pyright: ignore[reportUnusedFunction]
            """Get a comprehensive overview of the API data model.

            Returns detailed information about all entities, their fields, relationships,
            and how to traverse the data graph. Always call this first to understand
            the available data and operations.
            """
            model_description = self.describe_model()
            return {
                "title": self.title,
                "description": self.description,
                "entity_count": len(self.entities),
                "entities": list(self.entities.keys()),
                "model": model_description,
                "usage_hint": (
                    "Use the model information above to understand how to query the data. "
                    "Each entity has fields and relationships. Relationships must be resolved "
                    "separately using their specific resolver endpoints."
                ),
            }

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

            return cls

        return decorator(cls) if cls else decorator

    def _register_relationships(self, cls: type[EnrichModel]) -> None:
        """
        Register relationships for an entity class.

        Args:
            cls: The entity class to process
        """
        self.relationships[cls.__name__] = cls.relationships()

    def describe_model(self) -> str:
        """
        Generate a comprehensive description of the entire data model.

        Returns:
            A formatted string containing all entities, their fields, and relationships.
        """
        lines: list[str] = []

        # Add title
        lines.append(f"# Data Model: {self.title}")
        if self.description:
            lines.append(self.description)
        lines.append("")

        # Add table of contents
        if self.entities:
            lines.append("## Entities")
            for entity_name in sorted(self.entities.keys()):
                lines.append(f"- [{entity_name}](#{entity_name.lower()})")
            lines.append("")
        else:
            lines.append("*No entities registered*")
            return "\n".join(lines)

        # Add each entity
        for entity_name, entity_cls in sorted(self.entities.items()):
            lines.append(f"## {entity_name}")
            description = entity_cls.__doc__ or "No description available"
            lines.append(description.strip())
            lines.append("")

            # Fields section
            field_lines: list[str] = []
            for field_name, field in entity_cls.model_fields.items():
                # Skip relationship fields, we'll handle them separately
                if field_name in entity_cls.relationship_fields():
                    continue

                # Get field type and description
                field_type = "Any"  # Default type if annotation is None
                if field.annotation is not None:
                    field_type = str(field.annotation)  # Always safe fallback
                    if hasattr(field.annotation, "__name__"):
                        field_type = field.annotation.__name__
                field_desc = field.description

                # Format field info
                field_lines.append(f"- **{field_name}** ({field_type}): {field_desc}")

            if field_lines:
                lines.append("### Fields")
                lines.extend(field_lines)
                lines.append("")

            # Relationships section
            rel_lines: list[str] = []
            rel_fields = entity_cls.relationship_fields()
            for field_name in rel_fields:
                field = entity_cls.model_fields[field_name]
                rel = field.default
                target_type = "Any"  # Default type if annotation is None
                if field.annotation is not None:
                    target_type = str(field.annotation)  # Always safe fallback
                    if hasattr(field.annotation, "__name__"):
                        target_type = field.annotation.__name__
                rel_desc = rel.description

                rel_lines.append(f"- **{field_name}** → {target_type}: {rel_desc}")

            if rel_lines:
                lines.append("### Relationships")
                lines.extend(rel_lines)
                lines.append("")

        return "\n".join(lines)

    def resource(
        self,
        func: Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Callable[..., Any] | DecoratorCallable:
        """
        Register a function as an MCP resource.

        Can be used as:
            @app.resource
            async def my_resource():
                '''Resource description in docstring'''
                ...

        Or with explicit parameters:
            @app.resource(name="custom_name", description="Custom description")
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

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            # Get name and description
            resource_name = name or fn.__name__
            resource_desc = description or fn.__doc__

            # Check for description
            if not resource_desc:
                raise ValueError(
                    f"Resource '{resource_name}' must have a description. "
                    f"Provide it via @app.resource(description=...) or function docstring."
                )

            # Strip docstring if used
            if resource_desc == fn.__doc__ and resource_desc:
                resource_desc = resource_desc.strip()

            # Store the resource for testing
            self.resources[resource_name] = fn
            # Create and apply the MCP tool decorator
            mcp_tool = self.mcp.tool(name=resource_name, description=resource_desc)
            return mcp_tool(fn)

        # If called without parentheses (@app.resource)
        if func is not None:
            return decorator(func)

        # If called with parentheses (@app.resource())
        return cast("DecoratorCallable", decorator)

    def run(
        self, *, transport: str | None = None, mount_path: str | None = None, **options: Any
    ) -> Any:
        """
        Start the MCP server.

        Args:
            **options: Options to pass to the FastMCP run method

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

        # Run the MCP server
        return self.mcp.run(**options)
