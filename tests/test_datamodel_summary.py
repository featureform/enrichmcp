from enrichmcp.datamodel import DataModelSummary, ModelDescription


def test_datamodelsummary_str_no_entities() -> None:
    model = ModelDescription(title="M", description="", entities=[])
    summary = DataModelSummary(
        title="Empty",
        description="A test",
        entity_count=0,
        entities=[],
        model=str(model),
        usage_hint="HINT",
    )
    expected = "\n".join(
        [
            "# Empty",
            "A test",
            "",
            "**Entity count:** 0",
            "",
            str(model),
            "",
            "HINT",
        ]
    )
    assert str(summary) == expected


def test_datamodelsummary_str_sorted_entities() -> None:
    model = ModelDescription(title="M", description="", entities=[])
    summary = DataModelSummary(
        title="Test",
        description="",
        entity_count=3,
        entities=["B", "A", "C"],
        model=str(model),
        usage_hint="HINT",
    )
    text = str(summary)
    lines = text.splitlines()
    idx = lines.index("## Entities")
    assert lines[idx + 1 : idx + 4] == ["- A", "- B", "- C"]
    assert lines[-1] == "HINT"
