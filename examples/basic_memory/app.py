"""Simple API demonstrating the in-memory note utilities.

This example exposes a tiny CRUD interface for notes grouped into a single
``MemoryProject``. Notes are stored in ``./data`` using ``FileMemoryStore``
which writes Markdown files with YAML front matter. Listing notes only returns
their identifiers and titles while ``get_note`` returns the full content.
"""

from pathlib import Path

# The example-specific storage utilities live next to this file so that the
# main ``enrichmcp`` package remains lightweight.
# Import the lightweight note storage utilities from the current directory.
from memory import (
    FileMemoryStore,
    MemoryNote,
    MemoryNoteSummary,
    MemoryProject,
)

from enrichmcp import EnrichMCP

store = FileMemoryStore(Path(__file__).parent / "data")
project = MemoryProject("demo", store)

app = EnrichMCP(title="Basic Memory API", description="Manage simple notes")


@app.entity
class Note(MemoryNote):
    """A note stored in the demo project."""


@app.entity
class NoteSummary(MemoryNoteSummary):
    """Minimal note information returned from :func:`list_notes`."""


@app.create
async def create_note(
    title: str,
    content: str,
    tags: list[str] | None = None,
    note_id: str | None = None,
) -> Note:
    """Create or replace a note."""
    note = project.create_note(title, content, tags, note_id=note_id)
    return Note.model_validate(note.model_dump())


@app.retrieve
async def get_note(note_id: str) -> Note:
    """Retrieve a single note by its identifier."""
    note = project.get_note(note_id)
    if note is None:
        raise ValueError("note not found")
    return note


@app.retrieve
async def list_notes(page: int = 1, page_size: int = 10) -> list[NoteSummary]:
    """Return a paginated list of notes."""
    return project.list_notes(page, page_size)


if __name__ == "__main__":
    app.run()
