"""
APIs Tool MCP Server
Exposes GitHub API calls as MCP tools.
"""
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("apis-tool")

GITHUB_API = "https://api.github.com"
HEADERS = {"Accept": "application/vnd.github+json"}


@mcp.tool()
def get_user_info(username: str) -> str:
    """Get public profile info for a GitHub user."""
    try:
        resp = httpx.get(f"{GITHUB_API}/users/{username}", headers=HEADERS, timeout=10)
        if resp.status_code == 404:
            return f"Error: GitHub user '{username}' not found."
        data = resp.json()
        return (
            f"Name: {data.get('name') or username}\n"
            f"Bio: {data.get('bio') or 'N/A'}\n"
            f"Public repos: {data.get('public_repos')}\n"
            f"Followers: {data.get('followers')}\n"
            f"Location: {data.get('location') or 'N/A'}\n"
            f"Profile: {data.get('html_url')}"
        )
    except Exception as e:
        return f"Error fetching user info: {e}"


@mcp.tool()
def get_repo_info(owner: str, repo: str) -> str:
    """Get details about a specific GitHub repository."""
    try:
        resp = httpx.get(f"{GITHUB_API}/repos/{owner}/{repo}", headers=HEADERS, timeout=10)
        if resp.status_code == 404:
            return f"Error: repository '{owner}/{repo}' not found."
        data = resp.json()
        return (
            f"Repo: {data.get('full_name')}\n"
            f"Description: {data.get('description') or 'N/A'}\n"
            f"Stars: {data.get('stargazers_count')}\n"
            f"Forks: {data.get('forks_count')}\n"
            f"Language: {data.get('language') or 'N/A'}\n"
            f"URL: {data.get('html_url')}"
        )
    except Exception as e:
        return f"Error fetching repo info: {e}"


@mcp.tool()
def list_user_repos(username: str, limit: int = 5) -> str:
    """List a GitHub user's public repositories, most recently updated first."""
    try:
        resp = httpx.get(
            f"{GITHUB_API}/users/{username}/repos",
            headers=HEADERS,
            params={"sort": "updated", "per_page": limit},
            timeout=10,
        )
        if resp.status_code == 404:
            return f"Error: GitHub user '{username}' not found."
        repos = resp.json()
        if not repos:
            return f"No public repos found for '{username}'."
        return "\n".join(f"{r['name']} ({r.get('stargazers_count', 0)}⭐)" for r in repos)
    except Exception as e:
        return f"Error listing repos: {e}"


if __name__ == "__main__":
    mcp.run()