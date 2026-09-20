"""One-tool LibreChat MCP shell for Compliance Agent v1."""
from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, EmbeddedResource, TextContent, TextResourceContents
from pydantic import ConfigDict

from .agent import answer
from .ui_cards import render_fleet_card

mcp = FastMCP(
    "Compliance Agent v1",
    instructions=(
        "Read-only frontend bridge to the dedicated AgentCore Harness-backed Compliance Agent v1. "
        "Use ask_compliance_agent_v1 for current four-account S3 Block Public Access or restricted SSH status, explanation, and no-change planning. "
        "No remediation or generic AWS tool is exposed."
    ),
)


@mcp.tool()
def ask_compliance_agent_v1(request: str) -> CallToolResult:
    """Answer one AWS compliance request using live four-account Config evidence and AgentCore Harness reasoning."""
    value = answer(request)
    content = [
        TextContent(type="text", text=json.dumps(value, separators=(",", ":"), sort_keys=True)),
    ]
    lower = request.lower()
    if not any(token in lower for token in ("fix ", "apply ", "execute ", "remediate ")):
        content.append(
            EmbeddedResource(
                type="resource",
                resource=TextResourceContents(
                    uri="ui://compliance-agent-v1/fleet-status",
                    mimeType="text/html",
                    text=render_fleet_card(value["evidence"]),
                ),
            )
        )
    return CallToolResult(content=content, structuredContent=value)


# Fail closed on unexpected/coerced MCP arguments without mutating FastMCP settings.
# This configures the generated tool argument model, which is the intended
# Pydantic boundary used by the existing repo MCP adapters.
for tool in mcp._tool_manager.list_tools():
    model = tool.fn_metadata.arg_model
    model.model_config = ConfigDict(extra="forbid", strict=True)
    model.model_rebuild(force=True)
    tool.parameters = model.model_json_schema()


if __name__ == "__main__":
    mcp.run(transport="stdio")
