"""
Chat Interface — FastAPI wrapper around the MCP Assistant.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from client.assistant import MCPAssistant

assistant: MCPAssistant | None = None

# session_id -> conversation history list
sessions_store: dict[str, list[dict]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connect to all MCP servers once, when the API server starts."""
    global assistant
    assistant = MCPAssistant()
    await assistant.connect_all()
    print("MCP Assistant connected and ready.")
    yield
    await assistant.close()


app = FastAPI(title="MCP AI Assistant", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    reply = await assistant.chat(request.message, session_id=request.session_id)
    return ChatResponse(reply=reply)


@app.get("/health")
async def health_check():
    return {"status": "ok", "servers_connected": list(assistant.sessions.keys())}