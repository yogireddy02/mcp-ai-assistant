# MCP-Powered AI Assistant

An AI assistant that connects to external tools, APIs, and databases using the Model Context Protocol (MCP). Built as a hands-on learning project covering MCP server architecture, agentic tool-calling, and multi-turn session memory.

## Architecture
User → Chat Interface (FastAPI) → MCP AI Assistant → MCP Server/Router
↓
File Tool          Database Tool          APIs Tool
(Agent)            (Agent)                (Agent)
↓
Context Manager (session memory)
↓
LLM (Groq — openai/gpt-oss-20b)
↓
Final Response

## Features

- **3 independent MCP servers**, each a standalone process:
  - `servers/file_server.py` — sandboxed file read/write/list operations
  - `servers/db_server.py` — SQLite query tool (SELECT-only, with schema introspection)
  - `servers/api_server.py` — GitHub API lookups (user info, repo info, repo listing)
- **Agentic tool-calling loop** — the LLM can chain multiple tool calls (e.g. check schema, then query) before answering
- **Per-session conversation memory** — isolated context per user/session, so concurrent conversations don't leak into each other
- **Two implementations of the client/router**, for comparison:
  - `client/assistant.py` — hand-built MCP client (manual tool discovery, routing, and agent loop)
  - `client/assistant_langchain.py` — same functionality using LangChain + LangGraph's `create_agent`
- **FastAPI chat interface** (`client/server.py`) exposing `/chat` and `/health` endpoints
- **Dockerized** for portable deployment

## Tech Stack

Python · FastAPI · MCP SDK · Groq API (Llama/gpt-oss models) · LangChain · LangGraph · SQLite · Docker

## Setup

1. Clone the repo and create a virtual environment:
```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r requirements.txt
```

2. Add your free Groq API key ([console.groq.com](https://console.groq.com)) to a `.env` file:

GROQ_API_KEY=your_key_here

3. Run the terminal assistant directly:
```bash
   python client/assistant.py
```

   Or run the FastAPI server:
```bash
   uvicorn client.server:app --reload --port 8000
```

## Running with Docker

```bash
docker build -t mcp-ai-assistant .
docker run -p 8000:8000 --env-file .env mcp-ai-assistant
```

## API Usage

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me all users in the database", "session_id": "user-1"}'
```

## What I Learned

This project was built to understand MCP's client-server architecture from first principles — writing the tool discovery, routing, and agent loop by hand before refactoring to LangChain, in order to understand exactly what the framework automates.