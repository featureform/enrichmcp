"""Utility for annotating function parameters with extra metadata."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - import for type hints
    from collections.abc import Iterable


@dataclass
class EnrichParameter:
    """Metadata container for function parameters.

    When a parameter's default value is an instance of ``EnrichParameter`` the
    metadata contained here is appended to the generated tool description. The
    ``default`` attribute is **not** used as the runtime default value; it simply
    provides a placeholder so function signatures remain valid.
    """

    default: Any | None = None
    description: str | None = None
    examples: Iterable[Any] | None = None
    metadata: dict[str, Any] = dataclass_field(default_factory=dict)

    def __iter__(self) -> Iterable[Any]:  # pragma: no cover - convenience
        yield self.default
