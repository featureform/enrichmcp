"""Redis integration for EnrichMCP.

This package provides Redis search capabilities for EnrichMCP applications,
including automatic index creation, document storage, and MCP resource generation.
"""

from .app import EnrichMCP
from .field import Field
from .model import EnrichModel
from .relationship import Relationship

__all__ = ["EnrichMCP", "EnrichModel", "Field", "Relationship"]
