from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - for type checking only
    from .app import EnrichMCP


class ToolKind(str, Enum):
    """Kinds of MCP tools."""

    RETRIEVER = "retriever"
    CREATOR = "creator"
    UPDATER = "updater"
    DELETER = "deleter"
    RESOLVER = "resolver"


@dataclass
class ToolDef:
    """Definition of an MCP tool."""

    kind: ToolKind
    name: str
    description: str

    def final_description(self, app: EnrichMCP) -> str:
        """Return the description with standard usage prefix."""
        prefix = (
            f"This is a {self.kind.value} for the {app.title} server. "
            f"Use it after calling {app.data_model_tool_name()}."
        )
        return f"{prefix} {self.description}".strip()
