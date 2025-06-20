# OpenAI MCP Chat Agent

An interactive command-line agent that connects to an MCP server and converses using either OpenAI or a local Ollama model.

## Setup

```bash
cd openai_chat_agent
uv pip install -r requirements.txt
cp .env.example .env  # set OPENAI_API_KEY or adjust OLLAMA_MODEL
uv run app.py
```

`config.json` points to the `shop_api` example so everything runs locally by default. If `OPENAI_API_KEY` is not provided the agent uses the model specified by `OLLAMA_MODEL` (default `llama3`). An Ollama server must be running when using this mode.
