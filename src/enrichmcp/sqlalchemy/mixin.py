"""
SQLAlchemy mixin for EnrichMCP integration.

Provides functionality to convert SQLAlchemy models to EnrichModel representations.
"""

from typing import Any, cast

from pydantic import Field, create_model
from sqlalchemy import inspect  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import DeclarativeBase  # pyright: ignore[reportMissingImports]
from sqlalchemy.sql.type_api import TypeEngine  # pyright: ignore[reportMissingImports]

from enrichmcp import EnrichModel, Relationship


class EnrichSQLAlchemyMixin:
    """
    Mixin that enables SQLAlchemy models to be converted to EnrichModel representations.

    When a SQLAlchemy model inherits from this mixin and is registered with @app.entity,
    it will automatically generate an EnrichModel representation with proper field types
    and descriptions from the SQLAlchemy column metadata.
    """

    @classmethod
    def __enrich_model__(cls) -> type[EnrichModel]:
        """
        Convert this SQLAlchemy model to an EnrichModel representation.

        This method introspects the SQLAlchemy model and creates a corresponding
        EnrichModel with fields and relationships based on the SQLAlchemy metadata.

        Returns:
            A dynamically created EnrichModel class
        """
        if not issubclass(cls, DeclarativeBase):
            raise TypeError(f"{cls.__name__} must inherit from SQLAlchemy DeclarativeBase")

        # Get SQLAlchemy mapper
        mapper = inspect(cls)

        # Build field definitions for the EnrichModel
        field_definitions: dict[str, Any] = {}

        # Process columns
        for column_prop in mapper.column_attrs:
            column = column_prop.columns[0]
            field_name = column_prop.key

            # Skip fields marked with exclude in info
            if column.info.get("exclude", False):
                continue

            # Get Python type from SQLAlchemy column type
            python_type = _sqlalchemy_type_to_python(column.type)

            # Handle nullable columns
            if column.nullable:
                python_type = python_type | None

            # Get description from column info
            description = column.info.get("description", f"{field_name} field")

            # Create Pydantic Field
            if column.default is not None or column.server_default is not None:
                # Has default value
                field_definitions[field_name] = (python_type, Field(description=description))
            else:
                # Required field
                field_definitions[field_name] = (python_type, Field(description=description))

        # Process relationships
        for rel_prop in mapper.relationships:
            field_name = rel_prop.key
            rel_info = rel_prop.info

            # Skip relationships marked with exclude
            if rel_info.get("exclude", False):
                continue

            # Get description
            description = rel_info.get(
                "description", f"Relationship to {rel_prop.mapper.class_.__name__}EnrichModel"
            )

            # Determine relationship type
            if rel_prop.uselist:
                # One-to-many or many-to-many relationship
                target_class_name = rel_prop.mapper.class_.__name__
                # Map to EnrichModel version of the class
                enrich_target_name = f"{target_class_name}EnrichModel"
                rel_type = list[enrich_target_name]  # Using string forward reference
            else:
                # One-to-one or many-to-one relationship
                target_class_name = rel_prop.mapper.class_.__name__
                # Map to EnrichModel version of the class
                enrich_target_name = f"{target_class_name}EnrichModel"
                rel_type = enrich_target_name

            # Create Relationship field
            field_definitions[field_name] = (rel_type, Relationship(description=description))

        # Get model documentation
        model_doc = cls.__doc__ or f"{cls.__name__} entity"

        # Create the EnrichModel class dynamically
        enrich_model_class = create_model(
            f"{cls.__name__}EnrichModel",
            __base__=EnrichModel,
            __doc__=model_doc,
            **field_definitions,
        )

        # Store reference to original SQLAlchemy model
        # Use setattr to ensure it's properly set on the class
        enrich_model_class._sqlalchemy_model = cls

        return enrich_model_class


def _sqlalchemy_type_to_python(sa_type: TypeEngine) -> type[Any]:
    """
    Convert SQLAlchemy type to Python type.

    Args:
        sa_type: SQLAlchemy TypeEngine instance

    Returns:
        Corresponding Python type
    """
    # Import here to avoid circular dependencies
    from datetime import date, datetime, time

    from sqlalchemy import (
        JSON,
        BigInteger,
        Boolean,
        Date,
        DateTime,
        Float,
        Integer,
        LargeBinary,
        String,
        Text,
        Time,
    )

    type_map = {
        Integer: int,
        String: str,
        Text: str,
        Boolean: bool,
        Float: float,
        DateTime: datetime,
        Date: date,
        Time: time,
        JSON: dict,
        LargeBinary: bytes,
        BigInteger: int,
    }

    # Check for exact type matches first
    for sa_class, py_type in type_map.items():
        if type(sa_type) is sa_class:
            return py_type

    # Check for inheritance
    for sa_class, py_type in type_map.items():
        if isinstance(sa_type, sa_class):
            return py_type

    # Default to Any for unknown types
    return cast("type[Any]", Any)
