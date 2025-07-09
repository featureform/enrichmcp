"""Data model summary types."""

from pydantic import BaseModel, Field


class DataModelSummary(BaseModel):
    """Summary of all entities registered with an :class:`~enrichmcp.EnrichMCP` app."""

    title: str = Field(description="Application title")
    description: str = Field(description="Application description")
    entity_count: int = Field(description="Number of registered entities")
    entities: list[str] = Field(description="Entity names")
    model: str = Field(description="Full Markdown model description")
    usage_hint: str = Field(description="Hint on how to use the model information")

    def __str__(self) -> str:  # pragma: no cover - simple formatting
        """Return a human-readable Markdown summary."""
        lines = [f"# {self.title}"]
        if self.description:
            lines.append(self.description)
        lines.append("")
        lines.append(f"**Entity count:** {self.entity_count}")
        if self.entities:
            lines.append("")
            lines.append("## Entities")
            for name in sorted(self.entities):
                lines.append(f"- {name}")
        lines.append("")
        lines.append(self.model)
        lines.append("")
        lines.append(self.usage_hint)
        return "\n".join(lines)
