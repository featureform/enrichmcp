"""Lightweight note storage used by the Basic Memory example.

The classes defined here implement a minimal project-based note system
that persists notes to disk. Each note is stored as a Markdown file with
YAML front matter so they can be easily edited outside of the example.
This module intentionally keeps the logic simple and is not part of the
public ``enrichmcp`` package. It merely supports the example API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import uuid4

import yaml
from pydantic import Field

from enrichmcp.entity import EnrichModel

if TYPE_CHECKING:  # pragma: no cover - used only for type hints
    from pathlib import Path


class MemoryNote(EnrichModel):
    """A single note entry.

    Parameters
    ----------
    id:
        Unique identifier for the note. ``MemoryStore`` implementations
        generate this value when a note is created.
    title:
        Short title summarizing the note.
    content:
        The full body of the note.
    tags:
        Optional list of tag strings for free-form categorisation.
    """

    id: str = Field(description="Unique note identifier")
    title: str = Field(description="Note title")
    content: str = Field(description="Note content")
    tags: list[str] = Field(default_factory=list, description="Optional tags")


class MemoryNoteSummary(EnrichModel):
    """Lightweight representation containing only ``id`` and ``title``."""

    id: str = Field(description="Unique note identifier")
    title: str = Field(description="Note title")


class MemoryStore(ABC):
    """Abstract storage backend for ``MemoryNote`` objects."""

    @abstractmethod
    def new_id(self) -> str:
        """Return a new unique note identifier."""

    @abstractmethod
    def save(self, project: str, note: MemoryNote) -> None:
        """Persist ``note`` under ``project``."""

    @abstractmethod
    def load(self, project: str, note_id: str) -> MemoryNote | None:
        """Retrieve a note by ``note_id`` or ``None`` if it does not exist."""

    @abstractmethod
    def list(self, project: str, page: int, page_size: int) -> list[MemoryNoteSummary]:
        """Return a paginated list of notes for ``project``."""

    @abstractmethod
    def delete(self, project: str, note_id: str) -> bool:
        """Remove the note if present and return ``True`` on success."""


class FileMemoryStore(MemoryStore):
    """Filesystem implementation of :class:`MemoryStore`.

    Each project is a folder below ``root`` and every note is stored as a
    ``<id>.md`` file containing YAML front matter for the title and tags
    followed by the note content.
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _project_dir(self, project: str) -> Path:
        path = self.root / project
        path.mkdir(parents=True, exist_ok=True)
        return path

    def new_id(self) -> str:  # pragma: no cover - simple wrapper
        return uuid4().hex

    def save(self, project: str, note: MemoryNote) -> None:
        path = self._project_dir(project) / f"{note.id}.md"
        frontmatter = yaml.safe_dump({"title": note.title, "tags": note.tags}, sort_keys=False)
        with path.open("w", encoding="utf-8") as f:
            f.write("---\n")
            f.write(frontmatter)
            f.write("---\n")
            f.write(note.content)

    def load(self, project: str, note_id: str) -> MemoryNote | None:
        path = self._project_dir(project) / f"{note_id}.md"
        if not path.exists():
            return None
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return None
        _, rest = text.split("---", 1)
        fm, content = rest.split("---", 1)
        meta = yaml.safe_load(fm) or {}
        return MemoryNote(
            id=note_id,
            title=meta.get("title", ""),
            tags=meta.get("tags", []),
            content=content.lstrip(),
        )

    def list(self, project: str, page: int, page_size: int) -> list[MemoryNoteSummary]:
        p = self._project_dir(project)
        files = sorted(p.glob("*.md"))
        start = (page - 1) * page_size
        end = start + page_size
        notes: list[MemoryNoteSummary] = []
        for file in files[start:end]:
            note = self.load(project, file.stem)
            if note:
                notes.append(MemoryNoteSummary(id=note.id, title=note.title))
        return notes

    def delete(self, project: str, note_id: str) -> bool:
        path = self._project_dir(project) / f"{note_id}.md"
        if path.exists():
            path.unlink()
            return True
        return False


class MemoryProject:
    """Groups notes under a project name and delegates storage actions."""

    def __init__(self, name: str, store: MemoryStore) -> None:
        self.name = name
        self.store = store

    def create_note(
        self,
        title: str,
        content: str,
        tags: list[str] | None = None,
        note_id: str | None = None,
    ) -> MemoryNote:
        """Create a new note or overwrite an existing one."""
        note = MemoryNote(
            id=note_id or self.store.new_id(),
            title=title,
            content=content,
            tags=tags or [],
        )
        self.store.save(self.name, note)
        return note

    def get_note(self, note_id: str) -> MemoryNote | None:
        return self.store.load(self.name, note_id)

    def list_notes(self, page: int = 1, page_size: int = 10) -> list[MemoryNoteSummary]:
        return self.store.list(self.name, page, page_size)

    def update_note(self, note_id: str, patch: dict[str, object]) -> MemoryNote:
        note = self.get_note(note_id)
        if note is None:
            raise KeyError(note_id)
        updated = note.model_copy(update=patch)
        self.store.save(self.name, updated)
        return updated

    def delete_note(self, note_id: str) -> bool:
        return self.store.delete(self.name, note_id)
