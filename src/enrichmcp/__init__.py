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
from typing import TYPE_CHECKING

from .app import EnrichMCP
from .cache import MemoryCache, RedisCache
from .context import EnrichContext
from .datamodel import (
    DataModelSummary,
    EntityDescription,
    FieldDescription,
    ModelDescription,
    RelationshipDescription,
)
from .entity import EnrichModel
from .lifespan import combine_lifespans
from .pagination import CursorParams, CursorResult, PageResult, PaginatedResult, PaginationParams
from .parameter import EnrichParameter
from .relationship import (
    Relationship,
)
from .tool import ToolDef, ToolKind

if TYPE_CHECKING:
    from .sqlalchemy import EnrichSQLAlchemyMixin, sqlalchemy_lifespan

# Optional SQLAlchemy integration
has_sqlalchemy: bool = False
try:  # pragma: no cover - optional dependency
    from .sqlalchemy import EnrichSQLAlchemyMixin, sqlalchemy_lifespan  # noqa: F401
except ImportError:  # pragma: no cover - optional dependency
    pass
else:
    has_sqlalchemy = True

__all__ = [
    "CursorParams",
    "CursorResult",
    "DataModelSummary",
    "EnrichContext",
    "EnrichMCP",
    "EnrichModel",
    "EnrichParameter",
    "EntityDescription",
    "FieldDescription",
    "MemoryCache",
    "ModelDescription",
    "PageResult",
    "PaginatedResult",
    "PaginationParams",
    "RedisCache",
    "Relationship",
    "RelationshipDescription",
    "ToolDef",
    "ToolKind",
    "__version__",
    "combine_lifespans",
]

# Add SQLAlchemy to exports if available
if has_sqlalchemy:
    __all__.extend(["EnrichSQLAlchemyMixin", "sqlalchemy_lifespan"])
