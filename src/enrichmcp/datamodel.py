"""Data model summary types."""

from pydantic import BaseModel, Field


class FieldDescription(BaseModel):
    """Description of a model field."""

    name: str
    type: str
    description: str
    mutable: bool = False

    def __str__(self) -> str:
        type_repr = self.type
        if self.mutable and "mutable" not in type_repr:
            type_repr = f"{type_repr}, mutable"
        return f"- **{self.name}** ({type_repr}): {self.description}"


class RelationshipDescription(BaseModel):
    """Description of a relationship field."""

    name: str
    target: str
    description: str

    def __str__(self) -> str:
        return f"- **{self.name}** → {self.target}: {self.description}"


class EntityDescription(BaseModel):
    """Description of a single entity."""

    name: str
    description: str
    fields: list[FieldDescription] = Field(default_factory=list)
    relationships: list[RelationshipDescription] = Field(default_factory=list)

    def __str__(self) -> str:
        lines = [f"## {self.name}", self.description, ""]
        if self.fields:
            lines.append("### Fields")
            lines.extend(str(f) for f in self.fields)
            lines.append("")
        if self.relationships:
            lines.append("### Relationships")
            lines.extend(str(r) for r in self.relationships)
            lines.append("")
        return "\n".join(lines)


class ModelDescription(BaseModel):
    """Structured representation of the entire data model."""

    title: str
    description: str
    entities: list[EntityDescription] = Field(default_factory=list)

    def __str__(self) -> str:
        lines = [f"# Data Model: {self.title}"]
        if self.description:
            lines.append(self.description)
        lines.append("")
        if self.entities:
            lines.append("## Entities")
            for e in sorted(self.entities, key=lambda ent: ent.name):
                lines.append(f"- [{e.name}](#{e.name.lower()})")
            lines.append("")
            for e in sorted(self.entities, key=lambda ent: ent.name):
                lines.append(str(e))
        else:
            lines.append("*No entities registered*")
        return "\n".join(lines)


class DataModelSummary(BaseModel):
    """Summary of all entities registered with an :class:`~enrichmcp.EnrichMCP` app."""

    title: str = Field(description="Application title")
    description: str = Field(description="Application description")
    entity_count: int = Field(description="Number of registered entities")
    entities: list[str] = Field(description="Entity names")
    model: str = Field(description="Full Markdown model description")
    usage_hint: str = Field(description="Hint on how to use the model information")

    def __str__(self) -> str:
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
        lines.append(str(self.model))
        lines.append("")
        lines.append(self.usage_hint)
        return "\n".join(lines)
