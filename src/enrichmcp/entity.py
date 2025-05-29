"""
Entity module for enrichmcp.

Provides the base class for entity models.
"""

from collections.abc import Callable
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict
from pydantic.main import IncEx
from typing_extensions import override

from .relationship import Relationship


class EnrichModel(BaseModel):
    """
    Base class for all EnrichMCP entity models.

    All entity models must inherit from this class to be
    registered with EnrichMCP.
    """

    # Allow arbitrary types for more flexibility
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        ignored_types=(Relationship,),
    )

    @classmethod
    def relationship_fields(cls) -> set[str]:
        return {k for k, v in cls.model_fields.items() if isinstance(v.default, Relationship)}

    @classmethod
    def relationships(cls) -> set[Relationship]:
        return {
            v.default for _, v in cls.model_fields.items() if isinstance(v.default, Relationship)
        }

    @classmethod
    def _add_fields_to_incex(cls, original: IncEx | None, fields_to_add: set[str]) -> IncEx:
        """Helper method to combine relationship fields with existing exclude specification.

        This only handles exclude=None or exclude as a set[str], and will raise a TypeError
        for other types.
        """
        if original is None:
            return cast("IncEx", fields_to_add)

        if isinstance(original, set):
            # Combine the sets
            return cast("IncEx", original.union(fields_to_add))

        # If we get here, it's a type we don't handle
        raise TypeError(f"Cannot combine fields with exclude of type {type(original).__name__}.")

    def describe(self) -> str:
        """
        Generate a human-readable description of this model.

        Returns:
            A formatted string containing model details, fields, and relationships.
        """
        lines: list[str] = []

        # Model name and description
        class_name = self.__class__.__name__
        description = self.__class__.__doc__ or "No description available"
        lines.append(f"# {class_name}")
        lines.append(f"{description.strip()}")
        lines.append("")

        # Fields section
        field_lines: list[str] = []
        for name, field in self.__class__.model_fields.items():
            # Skip relationship fields, we'll handle them separately
            if name in self.__class__.relationship_fields():
                continue

            # Get field type and description
            field_type = "Any"  # Default type if annotation is None
            if field.annotation is not None:
                field_type = str(field.annotation)  # Always safe fallback
                if hasattr(field.annotation, "__name__"):
                    field_type = field.annotation.__name__
            field_desc = field.description

            # Format field info
            field_lines.append(f"- **{name}** ({field_type}): {field_desc}")

        if field_lines:
            lines.append("## Fields")
            lines.extend(field_lines)
            lines.append("")

        # Relationships section
        rel_lines: list[str] = []
        rel_fields = self.__class__.relationship_fields()
        for name in rel_fields:
            field = self.__class__.model_fields[name]
            rel = field.default
            # Get target type and description
            target_type = "Any"  # Default type if annotation is None
            if field.annotation is not None:
                if hasattr(field.annotation, "__name__"):
                    target_type = field.annotation.__name__
                else:
                    target_type = str(field.annotation)
            rel_desc = rel.description

            rel_lines.append(f"- **{name}** → {target_type}: {rel_desc}")

        if rel_lines:
            lines.append("## Relationships")
            lines.extend(rel_lines)

        # Join all lines and return
        return "\n".join(lines)

    @override
    def model_dump_json(
        self,
        *,
        indent: int | None = None,
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        context: Any | None = None,
        by_alias: bool | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal["none", "warn", "error"] = True,
        fallback: Callable[[Any], Any] | None = None,
        serialize_as_any: bool = False,
    ) -> str:
        rel_fields = self.__class__.relationship_fields()
        exclude_set = self.__class__._add_fields_to_incex(exclude, rel_fields)

        return super().model_dump_json(
            indent=indent,
            include=include,
            exclude=exclude_set,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            fallback=fallback,
            serialize_as_any=serialize_as_any,
        )

    @override
    def model_dump(
        self,
        *,
        mode: Literal["json", "python"] | str = "python",
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        context: Any | None = None,
        by_alias: bool | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal["none", "warn", "error"] = True,
        fallback: Callable[[Any], Any] | None = None,
        serialize_as_any: bool = False,
    ) -> dict[str, Any]:
        rel_fields = self.__class__.relationship_fields()
        exclude_set = self.__class__._add_fields_to_incex(exclude, rel_fields)

        return super().model_dump(
            mode=mode,
            include=include,
            exclude=exclude_set,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            fallback=fallback,
            serialize_as_any=serialize_as_any,
        )
