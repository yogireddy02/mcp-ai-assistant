"""
Database Tool MCP Server
Exposes SQLite query operations as MCP tools.
"""
import os
import sqlite_utils
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("database-tool")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "sandbox", "app.db")
db = sqlite_utils.Database(DB_PATH)

# Seed a sample table if it doesn't exist yet
if "users" not in db.table_names():
    db["users"].insert_all([
        {"id": 1, "name": "Alice", "role": "admin"},
        {"id": 2, "name": "Bob", "role": "editor"},
        {"id": 3, "name": "Charlie", "role": "viewer"},
    ], pk="id")


@mcp.tool()
def list_tables() -> str:
    """List all tables in the database."""
    tables = db.table_names()
    return "\n".join(tables) if tables else "No tables found."


@mcp.tool()
def query(sql: str) -> str:
    """Run a read-only SQL SELECT query against the database and return results.
    Example: SELECT * FROM users
    The sql argument must be a single valid SQLite SELECT statement as a plain string."""
    if not sql.strip().lower().startswith("select"):
        return "Error: only SELECT queries are allowed."
    try:
        rows = list(db.query(sql))
        if not rows:
            return "No results."
        return "\n".join(str(row) for row in rows)
    except Exception as e:
        return f"Query error: {e}"


@mcp.tool()
def describe_table(table_name: str) -> str:
    """Show the column names and types for a given table."""
    if table_name not in db.table_names():
        return f"Error: table '{table_name}' does not exist."
    columns = db[table_name].columns
    return "\n".join(f"{c.name} ({c.type})" for c in columns)


if __name__ == "__main__":
    mcp.run()