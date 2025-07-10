from enrichmcp.datamodel import (
    EntityDescription,
    FieldDescription,
    ModelDescription,
    RelationshipDescription,
)


def test_description_str_functions() -> None:
    field = FieldDescription(
        name="id",
        type="int",
        description="Identifier",
        mutable=True,
    )
    rel = RelationshipDescription(
        name="owner",
        target="User",
        description="Item owner",
    )
    entity = EntityDescription(
        name="Item",
        description="A simple item",
        fields=[field],
        relationships=[rel],
    )
    model = ModelDescription(title="Demo", description="", entities=[entity])

    # Verify individual string representations
    assert str(field) == "- **id** (int, mutable): Identifier"
    assert str(rel) == "- **owner** \u2192 User: Item owner"
    entity_text = str(entity)
    assert "## Item" in entity_text
    assert "### Fields" in entity_text
    assert str(field) in entity_text
    assert "### Relationships" in entity_text
    assert str(rel) in entity_text

    model_text = str(model)
    assert "# Data Model: Demo" in model_text
    assert "- [Item](#item)" in model_text
    assert entity_text in model_text
