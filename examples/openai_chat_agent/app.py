"""Interactive OpenAI agent using MCPAgent.

This script connects an OpenAI chat model to an MCP server and keeps
conversation context using the agent's built-in memory.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from importlib import metadata
from typing import TYPE_CHECKING

import httpx
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from mcp.types import (
    CreateMessageRequestParams,
    CreateMessageResult,
    ErrorData,
    TextContent,
)
from mcp_use import MCPAgent, MCPClient
from packaging.version import Version

if TYPE_CHECKING:  # pragma: no cover - only for type hints
    from mcp import ClientSession

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

SYSTEM_MESSAGE = "You are a helpful assistant that talks to the user and uses tools via MCP."


def list_available_examples() -> dict[str, str]:
    """Return a mapping of example name to app path."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    examples: dict[str, str] = {}
    for entry in os.scandir(base_dir):
        if not entry.is_dir() or entry.name == "openai_chat_agent":
            continue
        app_path = os.path.join(entry.path, "app.py")
        if os.path.exists(app_path):
            examples[entry.name] = app_path
    return examples


def choose_example(examples: dict[str, str], preselected: str | None = None) -> str:
    """Prompt the user to choose an example."""
    names = sorted(examples)
    if preselected and preselected in examples:
        return preselected

    print("Available examples:")
    for idx, name in enumerate(names, 1):
        print(f"  {idx}. {name}")

    while True:
        choice = input("Select example by number or name: ").strip()
        if choice in examples:
            return choice
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(names):
                return names[index]
        print("Invalid selection, try again.")


def make_sampling_callback(llm: ChatOpenAI | ChatOllama):
    async def sampling_callback(
        context: ClientSession, params: CreateMessageRequestParams
    ) -> CreateMessageResult | ErrorData:
        lc_messages = []
        system_prompt = getattr(params, "systemPrompt", None)
        if system_prompt:
            lc_messages.append(SystemMessage(content=system_prompt))
        for msg in params.messages:
            content = msg.content.text
            if msg.role == "assistant":
                lc_messages.append(AIMessage(content=content))
            else:
                lc_messages.append(HumanMessage(content=content))

        try:
            logger.info(f"Sampling with messages: {lc_messages}")
            max_tokens = getattr(params, "maxTokens", None)
            stop_sequences = getattr(params, "stopSequences", None)
            result_msg = await llm.ainvoke(
                lc_messages,
                temperature=params.temperature,
                max_tokens=max_tokens,
                stop=stop_sequences,
            )
        except Exception as exc:
            logger.error(f"Failed to invoke llm for sampling: {exc}")
            return ErrorData(code=400, message=str(exc))

        text = getattr(result_msg, "content", str(result_msg))
        model_name = getattr(llm, "model", "llm")
        logger.info(f"Sampling result: {text}")
        return CreateMessageResult(
            content=TextContent(text=text, type="text"),
            model=model_name,
            role="assistant",
        )

    return sampling_callback


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
    available_examples = list_available_examples()

    parser = argparse.ArgumentParser(description="Interactive MCP Chat Agent")
    parser.add_argument(
        "--example",
        help="Example to run (default: prompt for selection)",
    )
    args = parser.parse_args()

    example_name = choose_example(available_examples, args.example)
    server_path = available_examples[example_name]

    config = {"mcpServers": {example_name: {"command": "python", "args": [server_path]}}}

    openai_key = os.getenv("OPENAI_API_KEY")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")

    print("Initializing chat...")

    if openai_key:
        llm = ChatOpenAI(model="gpt-4o")
    else:
        await ensure_ollama_running(ollama_model)
        llm = ChatOllama(model=ollama_model)

    try:
        mcp_use_version = metadata.version("mcp_use")
    except metadata.PackageNotFoundError:  # pragma: no cover - dev env only
        mcp_use_version = "0"

    if Version(mcp_use_version) > Version("1.3.6"):
        client = MCPClient(config, sampling_callback=make_sampling_callback(llm))
    else:
        logger.warning(
            "mcp-use %s does not support sampling, install >1.3.6. Disabling sampling callback",
            mcp_use_version,
        )
        client = MCPClient(config)

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
