"""
SQLAlchemy integration for EnrichMCP.

This module provides utilities to convert SQLAlchemy models to EnrichModel representations.
"""

from .mixin import EnrichSQLAlchemyMixin

__all__ = ["EnrichSQLAlchemyMixin"]
