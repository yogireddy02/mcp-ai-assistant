"""
MCP AI Assistant — Router/Client
Connects to multiple MCP servers, lets Groq decide which tools to call,
executes them, and returns a final answer.
"""
import asyncio
import json
import os
from contextlib import AsyncExitStack

from dotenv import load_dotenv
from groq import Groq
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- Define our three MCP servers ---
SERVERS = {
    "file-tool": StdioServerParameters(command="python", args=["servers/file_server.py"]),
    "database-tool": StdioServerParameters(command="python", args=["servers/db_server.py"]),
    "apis-tool": StdioServerParameters(command="python", args=["servers/api_server.py"]),
}


class MCPAssistant:
    def __init__(self):
        self.sessions: dict[str, ClientSession] = {}   # server_name -> session
        self.tool_to_server: dict[str, str] = {}       # tool_name -> server_name
        self.exit_stack = AsyncExitStack()
        self.sessions_history: dict[str, list[dict]] = {}

    def _get_or_create_session(self, session_id: str) -> list[dict]:
        """Get existing conversation history for a session, or create a fresh one."""
        if session_id not in self.sessions_history:
            self.sessions_history[session_id] = [
                {
                    "role": "system",
                    "content": (
                        "You are an AI assistant with access to tools. "
                        "Always use the provided function-calling mechanism to call tools — "
                        "never write function calls as plain text. "
                        "You may call multiple tools in sequence if needed to fully answer the question. "
                        "Never guess or fabricate data. If a request is ambiguous or you lack context "
                        "to answer accurately, say so clearly instead of making up an answer, "
                        "or use a tool to look up the real information if one is available."
                    ),
                }
            ]
        return self.sessions_history[session_id]

    async def connect_all(self):
        """Spawn and connect to every MCP server, discover their tools."""
        for name, params in SERVERS.items():
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(params))
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self.sessions[name] = session

            tools_result = await session.list_tools()
            for tool in tools_result.tools:
                self.tool_to_server[tool.name] = name
            print(f"Connected to '{name}' — tools: {[t.name for t in tools_result.tools]}")

    def get_groq_tools(self):
        """Build the combined tool list in Groq/OpenAI function-calling format."""
        groq_tools = []
        # We need to re-fetch schemas synchronously from stored data,
        # so we cache them during connect_all instead — see build below.
        return groq_tools

    async def build_tool_schemas(self):
        """Fetch full tool schemas from every connected server, in Groq's expected format."""
        groq_tools = []
        for name, session in self.sessions.items():
            tools_result = await session.list_tools()
            for tool in tools_result.tools:
                groq_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema,
                    },
                })
        return groq_tools

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Route a tool call to the correct MCP server and execute it."""
        server_name = self.tool_to_server.get(tool_name)
        if not server_name:
            return f"Error: no server found for tool '{tool_name}'"
        session = self.sessions[server_name]
        result = await session.call_tool(tool_name, arguments)
        # MCP tool results come back as a list of content blocks
        return "\n".join(block.text for block in result.content if hasattr(block, "text"))

    async def chat(self, user_message: str, session_id: str = "default") -> str:
        """Full agentic loop with per-session conversation memory."""
        tools = await self.build_tool_schemas()
        history = self._get_or_create_session(session_id)

        history.append({"role": "user", "content": user_message})

        max_iterations = 5

        for _ in range(max_iterations):
            try:
                response = groq_client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=history,
                    tools=tools,
                    tool_choice="auto",
                )
            except Exception as e:
                return f"Sorry, I had trouble processing that request. ({e})"

            response_message = response.choices[0].message
            history.append(response_message)

            if not response_message.tool_calls:
                return response_message.content

            for tool_call in response_message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                print(f"  [Router] Calling '{tool_name}' via '{self.tool_to_server[tool_name]}' with {arguments}")

                tool_result = await self.call_tool(tool_name, arguments)

                history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                })

        return "Sorry, I couldn't complete that request within the tool-call limit."
    async def close(self):
        await self.exit_stack.aclose()


async def main():
    assistant = MCPAssistant()
    await assistant.connect_all()
    print("\n MCP Assistant ready. Type 'exit' to quit.\n")

    try:
        while True:
            user_input = input("You: ")
            if user_input.lower() in ("exit", "quit"):
                break
            answer = await assistant.chat(user_input)
            print(f"Assistant: {answer}\n")
    finally:
        await assistant.close()


if __name__ == "__main__":
    asyncio.run(main())