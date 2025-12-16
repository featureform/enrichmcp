"""Fake data generator for dashboard development and testing."""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from .models import EntityInfo, ToolInfo


class FakeDataGenerator:
    """Generates realistic fake data for dashboard development."""

    def __init__(self) -> None:
        self.entity_names = ["User", "Product", "Order", "Category", "Review", "Payment"]
        self.tool_prefixes = [
            "get",
            "list",
            "search",
            "filter",
            "find",
            "create",
            "update",
            "delete",
        ]
        self.agent_types = ["Claude", "GPT-4", "Gemini", "Custom Agent", "Test Client"]
        self.user_agents = [
            "MCP Client/1.0",
            "EnrichMCP Dashboard/1.0",
            "Claude Desktop/1.2.3",
            "Custom Integration/2.1",
        ]

    def generate_entities(self, count: int = 6) -> list[EntityInfo]:
        """Generate fake entity information."""
        entities = []
        for _i, name in enumerate(self.entity_names[:count]):
            field_count = random.randint(5, 12)
            relationship_count = random.randint(1, 3)

            # Generate fake fields
            fields = {}
            for j in range(field_count):
                field_types = ["str", "int", "float", "bool", "datetime", "list[str]"]
                field_name = (
                    f"field_{j + 1}" if j > 3 else ["id", "name", "created_at", "status"][j]
                )
                fields[field_name] = random.choice(field_types)

            # Generate fake relationships
            relationships = {}
            other_entities = [e for e in self.entity_names if e != name]
            for j in range(relationship_count):
                rel_name = f"related_{other_entities[j % len(other_entities)].lower()}s"
                relationships[rel_name] = f"list[{other_entities[j % len(other_entities)]}]"

            entities.append(
                EntityInfo(
                    name=name,
                    description=f"{name} entity with comprehensive data model",
                    field_count=field_count,
                    relationship_count=relationship_count,
                    instance_count=random.randint(100, 10000),
                    last_accessed=datetime.now() - timedelta(minutes=random.randint(1, 1440)),
                    fields=fields,
                    relationships=relationships,
                )
            )
        return entities

    def generate_tools(self, entities: list[EntityInfo]) -> list[ToolInfo]:
        """Generate fake tool information based on entities."""
        tools = []

        # Generate entity-based tools
        for entity in entities:
            for prefix in self.tool_prefixes:
                if prefix in ["create", "update", "delete"] and random.random() > 0.3:
                    continue  # Not all entities have mutation tools

                tool_name = f"{prefix}_{entity.name.lower()}"
                if prefix == "list":
                    tool_name += "s"

                # Generate parameters based on tool type
                parameters = {}
                if prefix in ["get", "update", "delete"]:
                    parameters["id"] = {"type": "integer", "description": f"{entity.name} ID"}
                elif prefix in ["search", "filter"]:
                    parameters["query"] = {"type": "string", "description": "Search query"}
                    parameters["limit"] = {
                        "type": "integer",
                        "description": "Result limit",
                        "default": 10,
                    }

                tools.append(
                    ToolInfo(
                        name=tool_name,
                        description=(
                            f"{prefix.title()} {entity.name.lower()}"
                            f"{'s' if prefix == 'list' else ''}"
                        ),
                        parameters=parameters,
                        return_type=f"{entity.name}"
                        if prefix != "list"
                        else f"list[{entity.name}]",
                        call_count=random.randint(0, 1000),
                        avg_latency=random.uniform(50, 500),
                        error_rate=random.uniform(0, 5),
                        last_called=datetime.now() - timedelta(minutes=random.randint(1, 60))
                        if random.random() > 0.2
                        else None,
                        entity_name=entity.name,
                    )
                )

        # Add some system tools
        system_tools = [
            ToolInfo(
                name="explore_data_model",
                description="Get comprehensive data model information",
                parameters={},
                return_type="DataModelSummary",
                call_count=random.randint(50, 200),
                avg_latency=random.uniform(100, 300),
                error_rate=random.uniform(0, 1),
                last_called=datetime.now() - timedelta(minutes=random.randint(1, 30)),
                entity_name=None,
            )
        ]

        return tools + system_tools
