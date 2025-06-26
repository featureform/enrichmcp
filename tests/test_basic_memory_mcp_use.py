import json
import sys
import textwrap
from pathlib import Path

import pytest
from mcp_use import MCPClient


@pytest.mark.asyncio
async def test_basic_memory_mcp_use(tmp_path: Path) -> None:
    script = tmp_path / "app.py"
    # Paths to the repository root and example memory module
    repo_root = Path(__file__).resolve().parents[1]
    examples_dir = repo_root / "examples" / "basic_memory"
    script.write_text(
        textwrap.dedent(
            f'''
            import sys
            from pathlib import Path

            sys.path.insert(0, {str(repo_root / "src")!r})
            sys.path.insert(0, {str(examples_dir)!r})
            from memory import FileMemoryStore, MemoryNote, MemoryNoteSummary, MemoryProject
            from enrichmcp import EnrichMCP

            store = FileMemoryStore(Path(__file__).parent / "data")
            project = MemoryProject("demo", store)

            app = EnrichMCP(title="Test", description="Desc")

            @app.entity
            class Note(MemoryNote):
                """A note stored in the demo project."""

                pass

            @app.entity
            class NoteSummary(MemoryNoteSummary):
                """Minimal note representation."""

                pass

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
                """Get a note by ID."""
                note = project.get_note(note_id)
                if note is None:
                    raise ValueError("note not found")
                return Note.model_validate(note.model_dump())

            @app.retrieve
            async def list_notes(page: int = 1, page_size: int = 10) -> list[NoteSummary]:
                """List notes with pagination."""
                notes = project.list_notes(page, page_size)
                return [NoteSummary.model_validate(n.model_dump()) for n in notes]

            if __name__ == "__main__":
                app.run()
            '''
        )
    )

    config = {"mcpServers": {"app": {"command": sys.executable, "args": [str(script)]}}}
    client = MCPClient(config=config)
    session = await client.create_session("app")

    create_result = await session.connector.call_tool(
        "create_note", {"title": "First", "content": "Hello", "tags": []}
    )
    note = json.loads(create_result.content[0].text)

    update_result = await session.connector.call_tool(
        "create_note",
        {
            "note_id": note["id"],
            "title": "Updated",
            "content": "New text",
            "tags": ["x"],
        },
    )
    updated = json.loads(update_result.content[0].text)
    assert updated["title"] == "Updated"

    get_result = await session.connector.call_tool("get_note", {"note_id": note["id"]})
    fetched = json.loads(get_result.content[0].text)
    assert fetched["content"] == "New text"

    await client.close_all_sessions()
