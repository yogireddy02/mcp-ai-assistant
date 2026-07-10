"""
MCP AI Assistant — LangChain version.
Same 3 MCP servers, but tool discovery, routing, and the agent loop
are now handled by LangChain + LangGraph instead of hand-written code.
"""
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

load_dotenv()

# Same 3 servers as before, just declared in the adapter's expected format
SERVERS_CONFIG = {
    "file-tool": {
        "command": "python",
        "args": ["servers/file_server.py"],
        "transport": "stdio",
    },
    "database-tool": {
        "command": "python",
        "args": ["servers/db_server.py"],
        "transport": "stdio",
    },
    "apis-tool": {
        "command": "python",
        "args": ["servers/api_server.py"],
        "transport": "stdio",
    },
}


class LangChainMCPAssistant:
    def __init__(self):
        self.client = MultiServerMCPClient(SERVERS_CONFIG)
        self.agent = None
        self.sessions_history: dict[str, list] = {}

    async def connect_all(self):
        """Discover tools from all 3 MCP servers and build the LangGraph agent."""
        tools = await self.client.get_tools()
        print(f"Discovered {len(tools)} tools across all servers: {[t.name for t in tools]}")

        llm = ChatGroq(
            model="openai/gpt-oss-20b",
            api_key=os.getenv("GROQ_API_KEY"),
        )

        # create_react_agent builds the ENTIRE tool-calling loop for us —
        # this replaces the ~40 lines of manual loop code from assistant.py
        self.agent = create_agent(llm, tools)

    async def chat(self, user_message: str, session_id: str = "default") -> str:
        history = self.sessions_history.get(session_id, [])
        history.append({"role": "user", "content": user_message})

        result = await self.agent.ainvoke({"messages": history})

        # The agent returns the full updated message list; keep it for next turn
        self.sessions_history[session_id] = result["messages"]

        final_message = result["messages"][-1]
        return final_message.content

    async def close(self):
        pass  # MultiServerMCPClient manages its own subprocess lifecycle per-call


async def main():
    import asyncio
    assistant = LangChainMCPAssistant()
    await assistant.connect_all()
    print("\nLangChain MCP Assistant ready. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ("exit", "quit"):
            break
        answer = await assistant.chat(user_input)
        print(f"Assistant: {answer}\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())