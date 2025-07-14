"""Interactive OpenAI agent using MCPAgent.

This script connects an OpenAI chat model to an MCP server and keeps
conversation context using the agent's built-in memory.
"""

from __future__ import annotations

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
from mcp_use import MCPAgent, MCPClient, load_config_file
from packaging.version import Version

if TYPE_CHECKING:  # pragma: no cover - only for type hints
    from mcp import ClientSession

logger = logging.getLogger(__name__)

SYSTEM_MESSAGE = "You are a helpful assistant that talks to the user and uses tools via MCP."


def make_sampling_callback(llm: ChatOpenAI | ChatOllama):
    async def sampling_callback(
        context: ClientSession, params: CreateMessageRequestParams
    ) -> CreateMessageResult | ErrorData:
        lc_messages = []
        if params.system_prompt:
            lc_messages.append(SystemMessage(content=params.system_prompt))
        for msg in params.messages:
            content = msg.content.text
            if msg.role == "assistant":
                lc_messages.append(AIMessage(content=content))
            else:
                lc_messages.append(HumanMessage(content=content))

        try:
            result_msg = await llm.ainvoke(
                lc_messages,
                temperature=params.temperature,
                max_tokens=params.max_tokens,
                stop=params.stop_sequences,
            )
        except Exception as exc:  # pragma: no cover - runtime error handling
            return ErrorData(code=400, message=str(exc))

        text = getattr(result_msg, "content", str(result_msg))
        model_name = getattr(llm, "model", "llm")
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
    config_file = os.path.join(os.path.dirname(__file__), "config.json")

    openai_key = os.getenv("OPENAI_API_KEY")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")

    print("Initializing chat...")

    if openai_key:
        llm = ChatOpenAI(model="gpt-4o")
    else:
        await ensure_ollama_running(ollama_model)
        llm = ChatOllama(model=ollama_model)

    sampling_cb = make_sampling_callback(llm)

    try:
        mcp_use_version = metadata.version("mcp_use")
    except metadata.PackageNotFoundError:  # pragma: no cover - dev env only
        mcp_use_version = "0"

    if Version(mcp_use_version) > Version("1.3.7"):
        client = MCPClient(
            load_config_file(config_file),
            sampling_callback=sampling_cb,
        )
    else:
        logger.warning("mcp-use %s does not support sampling, disabling callback", mcp_use_version)
        client = MCPClient(load_config_file(config_file))

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
