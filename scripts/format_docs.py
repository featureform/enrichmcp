#!/usr/bin/env python3
"""
Format Python code blocks in markdown files using ruff.

This script extracts Python code blocks from markdown files,
formats them with ruff, and writes them back.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path


def extract_python_blocks(content: str) -> list[tuple[int, str]]:
    """Extract Python code blocks from markdown content.

    Returns list of (start_pos, code) tuples.
    """
    pattern = r"```python\n(.*?)\n```"
    blocks = []

    for match in re.finditer(pattern, content, re.DOTALL):
        blocks.append((match.start(1), match.group(1)))

    return blocks


def format_code_with_ruff(code: str) -> str:
    """Format Python code using ruff."""
    try:
        # Write code to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        # Format with ruff
        subprocess.run(
            [sys.executable, "-m", "ruff", "format", temp_path, "--quiet"],
            capture_output=True,
            text=True,
        )

        # Read formatted code
        with open(temp_path) as f:
            formatted = f.read()

        # Clean up
        Path(temp_path).unlink()

        # Remove trailing newline that ruff adds
        if formatted.endswith("\n"):
            formatted = formatted[:-1]

        return formatted

    except Exception as e:
        print(f"Warning: Could not format code block: {e}", file=sys.stderr)
        return code


def format_markdown_file(filepath: Path) -> bool:
    """Format Python code blocks in a markdown file.

    Returns True if file was modified.
    """
    print(f"Processing {filepath}...")

    with open(filepath) as f:
        original_content = f.read()

    # Extract code blocks
    blocks = extract_python_blocks(original_content)
    if not blocks:
        return False

    # Format each block and build new content
    new_content = original_content
    offset = 0

    for start_pos, code in blocks:
        # Skip empty blocks or just whitespace
        if not code.strip():
            continue

        formatted = format_code_with_ruff(code)

        # Replace in content
        if formatted != code:
            # Adjust position for previous replacements
            adjusted_pos = start_pos + offset
            new_content = (
                new_content[:adjusted_pos] + formatted + new_content[adjusted_pos + len(code) :]
            )
            offset += len(formatted) - len(code)

    # Write back if changed
    if new_content != original_content:
        with open(filepath, "w") as f:
            f.write(new_content)
        print(f"  ✓ Formatted {len(blocks)} code blocks")
        return True

    return False


def main():
    """Format Python code blocks in all markdown files."""
    if len(sys.argv) > 1:
        # Format specific files
        paths = [Path(arg) for arg in sys.argv[1:]]
    else:
        # Format all markdown files in docs/
        paths = list(Path("docs").rglob("*.md"))
        # Also format README.md
        if Path("README.md").exists():
            paths.append(Path("README.md"))

    modified_count = 0
    for path in paths:
        if path.exists() and format_markdown_file(path):
            modified_count += 1

    print(f"\nFormatted {modified_count} files")


if __name__ == "__main__":
    main()
