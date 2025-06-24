"""Hello World HTTP example using EnrichMCP."""

from enrichmcp import EnrichMCP


def main() -> None:
    app = EnrichMCP(title="Hello HTTP API", description="A simple HTTP example")

    @app.retrieve(description="Say hello over HTTP")
    async def hello_http() -> dict[str, str]:
        return {"message": "Hello over HTTP!"}

    print("Starting HTTP server on http://localhost:8000 ...")
    app.run(transport="streamable-http")


if __name__ == "__main__":
    main()
