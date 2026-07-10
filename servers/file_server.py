"""
File Tool MCP Server
Exposes filesystem operation as MCP tools.
"""

import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("file-tool")

# Restrict operations to a safe sandbox directory
SANDBOX_DIR = os.path.join(os.path.dirname(__file__), "..", "sandbox")
os.makedirs(SANDBOX_DIR, exist_ok=True)


def _safe_path(filename: str) -> str:
    """Prevent path traversal outside the sandbox."""
    path = os.path.abspath(os.path.join(SANDBOX_DIR, filename))
    if not path.startswith(os.path.abspath(SANDBOX_DIR)):
        raise ValueError("Access denied: path outside sandbox")
    return path

@mcp.tool()
def list_files() -> str:
    """List all files in the sandbox directory."""
    files = os.listdir(SANDBOX_DIR)
    return "\n".join(files) if files else "No files Found."

@mcp.tool()
def read_files(filename: str) -> str:
    """Read the contents of a file in the sandbox directory."""
    path = _safe_path(filename)
    if not os.path.exists(path):
        return f"Error: {filename} does not exist."
    with open(path,'r', encoding="UTF-8") as f:
        return f.read()
    
@mcp.tool()
def write_file(filename: str, content: str) -> str:
    """Write content to a file in the sandbox directory."""
    path = _safe_path(filename)
    with open(path,'w', encoding='UTF-8') as f:
        f.write(content)
    return f"Successfully wrote {len(content)} characters to {filename}."


if __name__ == "__main__":
    mcp.run()