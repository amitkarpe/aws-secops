"""One-tool LibreChat MCP shell for Compliance Agent v1."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from .agent import answer

mcp = FastMCP(
    "Compliance Agent v1",
    instructions=(
        "Read-only frontend bridge to the dedicated AgentCore Harness-backed Compliance Agent v1. "
        "Use ask_compliance_agent_v1 for current four-account S3 Block Public Access or restricted SSH status, explanation, and no-change planning. "
        "No remediation or generic AWS tool is exposed."
    ),
)


@mcp.tool()
def ask_compliance_agent_v1(request: str) -> dict:
    """Answer one AWS compliance request using live four-account Config evidence and AgentCore Harness reasoning."""
    return answer(request)


if __name__ == "__main__":
    mcp.run(transport="stdio")
