"""Interactive OpenAI agent using MCPAgent.

This script connects an OpenAI chat model to an MCP server and keeps
conversation context using the agent's built-in memory.
"""

from __future__ import annotations

import asyncio
import os

import httpx
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient

SYSTEM_MESSAGE = "You are a helpful assistant that talks to the user and uses tools via MCP."


async def ensure_ollama_running(model: str) -> None:
    """Check that an Ollama server is running."""
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            await client.get("http://localhost:11434/api/tags")
    except Exception:
        msg = (
            "Ollama server not detected. Install from https://ollama.com and "
            "start it using:\n\n"
            "    ollama serve &\n    ollama pull "
            f"{model}\n\n"
            "Alternatively set the OPENAI_API_KEY environment variable to use "
            "OpenAI instead of Ollama."
        )
        raise RuntimeError(msg) from None


async def run_memory_chat() -> None:
    """Run an interactive chat session with conversation memory enabled."""
    load_dotenv()
    config_file = os.path.join(os.path.dirname(__file__), "config.json")

    print("Initializing chat...")
    client = MCPClient.from_config_file(config_file)

    openai_key = os.getenv("OPENAI_API_KEY")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")

    if openai_key:
        llm = ChatOpenAI(model="gpt-4o")
    else:
        await ensure_ollama_running(ollama_model)
        llm = ChatOllama(model=ollama_model)

    agent = MCPAgent(
        llm=llm,
        client=client,
        max_steps=15,
        memory_enabled=True,
        system_prompt=SYSTEM_MESSAGE,
    )

    print("\n===== Interactive MCP Chat =====")
    print("Type 'exit' or 'quit' to end the conversation")
    print("Type 'clear' to clear conversation history")
    print("Type 'history' to display the conversation so far")
    print("=================================\n")

    try:
        while True:
            user_input = input("\nYou: ")
            command = user_input.lower()

            if command in ("exit", "quit"):
                print("Ending conversation...")
                break

            if command == "clear":
                agent.clear_conversation_history()
                print("Conversation history cleared.")
                continue

            if command == "history":
                for msg in agent.get_conversation_history():
                    role = getattr(msg, "type", "assistant").capitalize()
                    print(f"{role}: {msg.content}")
                continue

            print("\nAssistant: ", end="", flush=True)
            try:
                response = await agent.run(user_input)
                print(response)
            except Exception as exc:
                print(f"\nError: {exc}")
    finally:
        if client and client.sessions:
            await client.close_all_sessions()


if __name__ == "__main__":
    asyncio.run(run_memory_chat())
