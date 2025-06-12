"""
SQLAlchemy integration for EnrichMCP.

This module provides utilities to convert SQLAlchemy models to EnrichModel representations.
"""

from .auto import include_sqlalchemy_models
from .lifecycle import sqlalchemy_lifespan
from .mixin import EnrichSQLAlchemyMixin

__all__ = ["EnrichSQLAlchemyMixin", "include_sqlalchemy_models", "sqlalchemy_lifespan"]
