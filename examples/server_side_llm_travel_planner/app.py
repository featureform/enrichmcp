"""Travel planner example using server-side LLM sampling."""

import json
from typing import Annotated

from pydantic import Field

from enrichmcp import EnrichMCP, EnrichModel, prefer_fast_model

app = EnrichMCP(
    title="Travel Planner",
    description="Suggest destinations based on user preferences using LLM sampling",
)


class Destination(EnrichModel):
    """Popular travel destination."""

    name: str = Field(description="Name of the destination")
    region: str = Field(description="Region of the world")
    summary: str = Field(description="Short description of the location")


DESTINATIONS = [
    Destination(
        name="Paris",
        region="Europe",
        summary="Romantic city known for art, fashion and the Eiffel Tower",
    ),
    Destination(
        name="Tokyo",
        region="Asia",
        summary="Bustling metropolis blending modern tech and ancient temples",
    ),
    Destination(
        name="New York",
        region="North America",
        summary="Iconic skyline, diverse food and world-class museums",
    ),
    Destination(
        name="Sydney",
        region="Australia",
        summary="Harbour city with famous opera house and beautiful beaches",
    ),
    Destination(
        name="Cape Town",
        region="Africa",
        summary="Mountain backdrop, coastal views and vibrant culture",
    ),
]


@app.retrieve
def list_destinations() -> list[Destination]:
    """Return the full list of available destinations."""

    return DESTINATIONS


@app.retrieve
async def plan_trip(
    preferences: Annotated[str, Field(description="Your travel preferences")],
) -> list[Destination]:
    """Return three destinations that best match the given preferences."""
    ctx = app.get_context()
    bullet_list = "\n".join(f"- {d.name}: {d.summary}" for d in DESTINATIONS)
    prompt = (
        "Select the three best destinations from the list below based on the "
        "given preferences. Reply with a JSON list of names only. "
        "The text should be directly parsable with json.loads in Python. "
        'Do NOT add ```json like markdown. Example response:\n["San Francisco"]'
        "\n\n\nPreferences: "
        f"{preferences}\n\n{bullet_list}"
    )
    result = await ctx.ask_llm(
        prompt,
        model_preferences=prefer_fast_model(),
        max_tokens=50,
    )
    names = json.loads(result.content.text)
    return [d for d in DESTINATIONS if d.name in names]


if __name__ == "__main__":
    app.run()
