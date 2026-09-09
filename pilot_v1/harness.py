"""Small wrapper for reproducible AgentCore Harness invocation."""

from __future__ import annotations

import json
import subprocess
import uuid
from typing import Any

from .config import PilotConfig


def _response_text(value: Any) -> str:
    if not isinstance(value, str):
        raise RuntimeError("AgentCore Harness returned no text response")
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        decoded = value
    if isinstance(decoded, dict):
        decoded = decoded.get("text", "")
    if not isinstance(decoded, str) or not decoded.strip():
        raise RuntimeError("AgentCore Harness returned no text response")
    return decoded.strip()


def invoke(config: PilotConfig, prompt: str, *, cli: str = "agentcore") -> dict[str, Any]:
    config.require_harness()
    session_id = f"pilot-{uuid.uuid4()}"
    command = [
        cli,
        "invoke",
        "--harness-arn",
        config.harness_arn,
        "--region",
        config.region,
        "--session-id",
        session_id,
        "--json",
        "--prompt",
        prompt,
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError("AgentCore Harness invocation failed")
    events = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
    summary = next((event for event in reversed(events) if "success" in event), None)
    if not summary or summary.get("success") is not True:
        raise RuntimeError("AgentCore Harness returned no successful summary")
    response = _response_text(summary.get("response"))
    return {
        "response": response,
        "tool_calls": sum(1 for event in events if event.get("start", {}).get("toolUse")),
        "events": events,
        "session_id": session_id,
    }
