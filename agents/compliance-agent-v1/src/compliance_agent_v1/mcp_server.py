"""One-tool LibreChat MCP shell for Compliance Agent v1."""
from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, EmbeddedResource, TextContent, TextResourceContents
from pydantic import ConfigDict

from .agent import answer
from .scaled_findings import model_read
from .ui_cards import ALIASES, S3, SSH, render_capability_card, render_fleet_card

mcp = FastMCP(
    "Compliance Agent v1",
    instructions=(
        "Read-only evidence bridge used by the outer Compliance Agent v1. "
        "Use ask_compliance_agent_v1 for current four-account S3 Block Public Access or restricted SSH status, explanation, and no-change planning. "
        "This MCP itself exposes no remediation tool; the outer LibreChat agent may offer remediation only through its separate governed native-approval planner/executor path. "
        "Do not imply that the overall Compliance Agent cannot remediate when that governed path is available."
    ),
)


def _is_capability_request(request: str) -> bool:
    lower = request.strip().lower()
    return "capabilit" in lower or any(
        key in lower
        for key in (
            "s3_ssl", "s3 ssl", "s3_logging", "s3 logging",
            "s3_backup", "s3 backup", "restricted_ssh",
        )
    )


def _rich_status_model_text(request: str, value: dict) -> str | None:
    """Keep the model from duplicating the rich status card as Markdown."""
    lower = request.strip().lower()
    if _is_capability_request(request):
        return None
    is_status = "status" in lower and not any(
        token in lower for token in ("explain", "why", "plan", "identifier", "recommend")
    )
    if not is_status:
        return None

    checks = value.get("evidence", {}).get("checks", [])
    s3_bad = any(
        item.get("account_alias") in ALIASES
        and item.get("control") == S3
        and item.get("status") == "NON_COMPLIANT"
        for item in checks
        if isinstance(item, dict)
    )
    ssh_bad = any(
        item.get("account_alias") in ALIASES
        and item.get("control") == SSH
        and item.get("status") == "NON_COMPLIANT"
        for item in checks
        if isinstance(item, dict)
    )
    return (
        "Current fleet status is rendered in the attached native Ops card. "
        "Render the UI Resource Marker exactly once and do not repeat the status as Markdown, "
        "a second table, a list, or a second next-action line. The native card already contains "
        "the single authoritative next action."
    )


@mcp.tool()
def ask_compliance_agent_v1(request: str) -> CallToolResult:
    """Answer one AWS compliance request using live four-account Config evidence and AgentCore Harness reasoning."""
    value = answer(request)
    lower = request.lower()
    capability_request = _is_capability_request(request)
    rich_model_text = _rich_status_model_text(request, value)
    content = [
        TextContent(
            type="text",
            text=rich_model_text or json.dumps(value, separators=(",", ":"), sort_keys=True),
        ),
    ]
    if capability_request:
        content.append(
            EmbeddedResource(
                type="resource",
                resource=TextResourceContents(
                    uri="ui://compliance-agent-v1/capabilities",
                    mimeType="text/html",
                    text=render_capability_card(value["capabilities"]),
                ),
            )
        )
    elif not any(token in lower for token in ("fix ", "apply ", "execute ", "remediate ")):
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


@mcp.tool()
def query_synthetic_fleet_v1(
    mode: str,
    control_key: str | None = None,
    account_alias: str | None = None,
    config_status: str | None = None,
    exception_status: str | None = None,
    search: str | None = None,
    sort_by: str = "finding_id",
    sort_direction: str = "asc",
    page: int = 1,
    limit: int = 25,
) -> dict:
    """Read the synthetic 1K fleet as a summary, one bounded page, or an export receipt.

    Export mode generates CSV from backend truth but returns metadata only; CSV content is
    deliberately kept out of model context. This tool has no AWS or mutation capability.
    """
    return model_read(
        mode,
        control_key=control_key,
        account_alias=account_alias,
        config_status=config_status,
        exception_status=exception_status,
        search=search,
        sort_by=sort_by,
        sort_direction=sort_direction,
        page=page,
        limit=limit,
    )


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
