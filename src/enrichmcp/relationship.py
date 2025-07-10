"""
Relationship module for enrichmcp.

Provides field factories for defining entity relationships.
"""

from collections.abc import Callable
from typing import (
    Any,
    TypeVar,
    get_args,
    get_origin,
)

from .tool import ToolDef, ToolKind

T = TypeVar("T")


class Relationship:
    """
    Define a relationship between entities using a descriptor pattern.

    This allows for the @Entity.field.resolver pattern.

    Args:
        description: Description of the relationship
    """

    def __init__(self, *, description: str):
        self.description = description
        self.resolvers: list[tuple[str, Callable[..., Any]]] = []
        self.field_name: str | None = None
        self.owner_cls: type | None = None
        self.app: Any = None
        self.target_type: Any = None

    def __set_name__(self, owner: type, name: str) -> None:
        """Called when the descriptor is assigned to a class attribute."""
        self.field_name = name
        self.owner_cls = owner

        # Get the type annotation from the owner class
        if hasattr(owner, "__annotations__") and name in owner.__annotations__:
            self.target_type = owner.__annotations__[name]

        # Try to get app reference (will be set later if not available now)
        self.app = getattr(owner, "_app", None)

    def __get__(self, instance: Any | None, owner: type) -> Any:
        """Support both Class.field.resolver and instance.field access."""
        if instance is None:
            # Class access (User.posts) - return self to support .resolver
            return self

        # Instance access - this would be the actual relationship data
        # For now, just return None as we don't have query functionality yet
        return None

    def resolver(
        self, func: Callable[..., Any] | None = None, *, name: str | None = None
    ) -> Callable[..., Any]:
        """
        Register a resolver function for this relationship.

        Can be used as:
            @User.posts.resolver
            def get_posts(user_id: int) -> List[Post]:
                ...

        Or with a custom name:
            @User.posts.resolver(name="get_by_date")
            def get_posts_by_date(user_id: int, date: date) -> List[Post]:
                ...
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            # Get or create resolver name
            resolver_name = name or getattr(func, "__name__", "resolver")

            # Validate resolver return type
            self._validate_resolver_return_type(func)

            # Store the resolver
            self.resolvers.append((resolver_name, func))

            # If app is available, register as a resource
            if self.app and hasattr(self.app, "resource"):
                entity_name = self.owner_cls.__name__ if self.owner_cls else "Entity"
                field_name = self.field_name or "field"

                # Create resource name following convention
                resource_name = f"get_{entity_name.lower()}_{field_name}"
                if resolver_name != "get":
                    resource_name += f"_{resolver_name}"

                # Create description combining entity, relationship, and function doc
                func_doc = getattr(func, "__doc__", "")
                resource_description = (
                    f"Get {field_name} for {entity_name}. {self.description}. {func_doc}"
                ).strip()

                # Register with app's tool system using a ToolDef
                tool_def = ToolDef(
                    kind=ToolKind.RESOLVER,
                    name=resource_name,
                    description=resource_description,
                )
                return self.app._register_tool_def(func, tool_def)

            return func

        # Handle both @resolver and @resolver() forms
        if func is None:
            return decorator
        return decorator(func)

    def _validate_resolver_return_type(self, func: Callable[..., Any]) -> None:
        """
        Validate that the resolver's return type matches the relationship's type annotation.
        """
        if not self.target_type:
            return  # Can't validate without a target type

        # Get function's return type annotation
        func_annotations = getattr(func, "__annotations__", {})
        return_type = func_annotations.get("return")

        if not return_type:
            return  # Can't validate without return type

        # Direct comparison between return type and target type
        # This handles Union, Optional, pipe syntax, etc. without extraction
        if not self._is_compatible_type(return_type, self.target_type):
            func_name = getattr(func, "__name__", "resolver")
            raise TypeError(
                f"Resolver {func_name} returns {return_type} which is incompatible with "
                f"relationship type {self.target_type}"
            )

    # Method removed as it's no longer needed with the simplified validation approach

    def _is_compatible_type(self, return_type: Any, target_type: Any) -> bool:
        """Check if return_type is compatible with target_type."""
        # Handle string forward references
        if isinstance(return_type, str) or isinstance(target_type, str):
            # Can't reliably check string types at runtime
            return True

        # Check for non-type objects (numbers, strings, etc.)
        if (not isinstance(return_type, type) and not hasattr(return_type, "__origin__")) or (
            not isinstance(target_type, type) and not hasattr(target_type, "__origin__")
        ):
            # For non-types, we can't check compatibility reliably
            return True

        # Handle Optional and Union types
        return_origin = get_origin(return_type) if hasattr(return_type, "__origin__") else None
        target_origin = get_origin(target_type) if hasattr(target_type, "__origin__") else None

        # If both are union types, check if they're compatible
        if return_origin is not None and target_origin is not None:
            # Special case for Optional (Union with None)
            if self._is_optional_type(return_type) and self._is_optional_type(target_type):
                # Compare the non-None types
                return_args = [arg for arg in get_args(return_type) if arg is not type(None)]
                target_args = [arg for arg in get_args(target_type) if arg is not type(None)]
                if len(return_args) == 1 and len(target_args) == 1:
                    return self._is_compatible_type(return_args[0], target_args[0])

            # For now, just check if they're the same union type
            # More sophisticated union compatibility checking could be added here
            return return_type == target_type

        # If return type is Optional but target isn't, check if the non-None type is compatible
        if self._is_optional_type(return_type) and not self._is_optional_type(target_type):
            non_none_args = [arg for arg in get_args(return_type) if arg is not type(None)]
            if len(non_none_args) == 1:
                return self._is_compatible_type(non_none_args[0], target_type)

        # Check for subclass relationship for normal types
        try:
            if (
                isinstance(return_type, type)
                and isinstance(target_type, type)
                and issubclass(return_type, target_type)
            ):
                return True
        except TypeError:
            # Not class types, can't use issubclass
            pass

        # Check for identity
        return return_type == target_type

    def _is_optional_type(self, type_hint: Any) -> bool:
        """Check if a type hint is Optional (Union with None)."""
        if not hasattr(type_hint, "__origin__"):
            return False

        origin = get_origin(type_hint)
        args = get_args(type_hint)

        # Check if it's a union with None (Optional)
        is_union = str(origin).endswith("Union") or str(origin) == "types.UnionType"
        has_none = type(None) in args
        return bool(is_union and has_none)

    def is_resolved(self) -> bool:
        """Check if this relationship has at least one resolver."""
        return len(self.resolvers) > 0
