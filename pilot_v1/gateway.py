"""Minimal AWS-IAM AgentCore Gateway MCP client."""

from __future__ import annotations

import json
import subprocess
from typing import Any
from urllib.parse import urlparse


MCP_VERSION = "2025-03-26"


def _endpoint(gateway_url: str, region: str) -> str:
    parsed = urlparse(gateway_url)
    suffix = f".gateway.bedrock-agentcore.{region}.amazonaws.com"
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or not parsed.hostname.endswith(suffix)
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Gateway URL is not the expected AWS-managed endpoint")
    endpoint = gateway_url.rstrip("/")
    return endpoint if endpoint.endswith("/mcp") else f"{endpoint}/mcp"


def call_tool(
    gateway_url: str,
    region: str,
    profile: str,
    tool_name: str,
    arguments: dict[str, Any],
    *,
    request_id: str = "pilot-v1",
) -> dict[str, Any]:
    endpoint = _endpoint(gateway_url, region)
    exported = subprocess.run(
        ["aws", "--profile", profile, "--region", region, "configure", "export-credentials"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if exported.returncode != 0:
        raise RuntimeError("AWS credential provider failed")
    credentials = json.loads(exported.stdout)
    access_key = credentials.get("AccessKeyId")
    secret_key = credentials.get("SecretAccessKey")
    if not access_key or not secret_key:
        raise RuntimeError("AWS credential provider returned incomplete credentials")

    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        },
        separators=(",", ":"),
    )
    lines = [
        f'url = "{endpoint}"',
        'request = "POST"',
        f'aws-sigv4 = "aws:amz:{region}:bedrock-agentcore"',
        f'user = "{access_key}:{secret_key}"',
        'header = "Accept: application/json, text/event-stream"',
        'header = "Content-Type: application/json"',
        f'header = "MCP-Protocol-Version: {MCP_VERSION}"',
        f'data = "{payload.replace(chr(34), chr(92) + chr(34))}"',
        "silent",
        "show-error",
        'connect-timeout = "15"',
        'max-time = "60"',
    ]
    if credentials.get("SessionToken"):
        lines.append(f'header = "X-Amz-Security-Token: {credentials["SessionToken"]}"')
    completed = subprocess.run(
        ["curl", "--config", "-"],
        input="\n".join(lines) + "\n",
        check=False,
        capture_output=True,
        text=True,
        timeout=75,
    )
    credentials.clear()
    if completed.returncode != 0:
        raise RuntimeError("AgentCore Gateway request failed")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("AgentCore Gateway returned invalid JSON") from exc
    if not isinstance(result, dict):
        raise RuntimeError("AgentCore Gateway returned an invalid response")
    return result


def result_text(response: dict[str, Any]) -> str:
    blocks = response.get("result", {}).get("content", [])
    return "\n".join(
        block.get("text", "") for block in blocks if block.get("type") == "text"
    ).strip()
