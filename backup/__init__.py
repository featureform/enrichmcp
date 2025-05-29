"""
enrichmcp - A Python-first Framework for Exposing Structured Data to AI Agents.

Powered by Pydantic & the Model-Context Protocol.
"""

__version__ = "0.1.0"

from .app import EnrichMCP
from .context import EnrichContext
from .errors import NotFoundError, PermissionDeniedError, ValidationError
from .relationship import PaginatedResult, Relationship, RelationshipList, paginate

__all__ = [
    "EnrichContext",
    "EnrichMCP",
    "NotFoundError",
    "PaginatedResult",
    "PermissionDeniedError",
    "Relationship",
    "RelationshipList",
    "ValidationError",
    "paginate",
]
