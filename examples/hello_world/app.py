"""
Hello World example for EnrichMCP.

This is the simplest possible EnrichMCP application with a single resource
that returns "Hello, World!".
"""

from enrichmcp import EnrichMCP


def main():
    # Create the EnrichMCP application
    app = EnrichMCP(title="Hello World API", description="A simple API that says hello!")

    # Define a hello world resource
    @app.retrieve(description="Say hello to the world")
    async def hello_world() -> dict:
        """
        A simple resource that returns a hello world message.
        """
        return {"message": "Hello, World!", "status": "success"}

    # Run the server
    print("Starting the Hello World API...")
    app.run()


if __name__ == "__main__":
    main()
