"""
EnrichMCP: A framework for exposing structured data to AI agents.

This library provides a clean, declarative API for defining data models
as entities with relationships between them, making it easier for AI
assistants to interact with structured data.
"""

# Version handling
__version__: str
try:
    # If installed, setuptools_scm will have generated this
    from ._version import __version__  # pyright: ignore
except ImportError:
    try:
        # During development/editable installs
        from setuptools_scm import get_version  # pyright: ignore[reportMissingImports]

        __version__ = get_version(root="../..", relative_to=__file__)  # pyright: ignore[reportUnknownVariableType]
    except (ImportError, LookupError):
        # Fallback
        __version__ = "0.0.0+unknown"

# Public exports
from .app import EnrichMCP
from .context import EnrichContext
from .entity import EnrichModel
from .pagination import CursorParams, CursorResult, PageResult, PaginatedResult, PaginationParams
from .relationship import (
    Relationship,
)

__all__ = [
    "CursorParams",
    "CursorResult",
    "EnrichContext",
    "EnrichMCP",
    "EnrichModel",
    "PageResult",
    "PaginatedResult",
    "PaginationParams",
    "Relationship",
    "__version__",
]
