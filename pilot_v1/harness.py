"""Small wrapper for reproducible AgentCore Harness invocation."""

from __future__ import annotations

import json
import subprocess
import uuid
import time
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


def _tool_results(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for event in events:
        for item in event.get("delta", {}).get("results", []):
            text = item.get("text")
            if not isinstance(text, str):
                continue
            try:
                decoded = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(decoded, dict):
                results.append(decoded)
    return results


def invoke(
    config: PilotConfig, prompt: str, *, cli: str = "agentcore",
    system_prompt: str | None = None, explanation_only: bool = False,
) -> dict[str, Any]:
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
        "--verbose",
        "--prompt",
        prompt,
    ]
    if system_prompt is not None:
        command.extend(["--system-prompt", system_prompt])
    if explanation_only:
        # Empty strings are omitted by the CLI. This exact name matches no
        # built-in or registered MCP tool; it grants no effective tool access.
        command.extend([
            "--allowed-tools", "__pilot_explanation_no_tools__",
            "--model-id", config.model_id, "--model-provider", "bedrock",
            "--max-tokens", "700", "--max-iterations", "1",
        ])
    started = time.monotonic()
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Harness timed out after 90 seconds; evidence retained") from exc
    if completed.returncode != 0:
        raise RuntimeError("AgentCore Harness invocation failed")
    events = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
    tool_calls = sum(1 for event in events if event.get("start", {}).get("toolUse"))
    if explanation_only and (tool_calls or _tool_results(events)):
        raise RuntimeError("specialist explanation attempted a tool call; result rejected")
    summary = next((event for event in reversed(events) if "success" in event), None)
    if not summary or summary.get("success") is not True:
        raise RuntimeError("AgentCore Harness returned no successful summary")
    try:
        response = _response_text(summary.get("response"))
    except RuntimeError:
        response = "".join(
            event.get("delta", {}).get("text", "")
            for event in events
            if isinstance(event.get("delta", {}).get("text"), str)
        ).strip()
        if not response:
            raise RuntimeError("AgentCore Harness returned no text response")
    return {
        "response": response,
        "tool_calls": tool_calls,
        "tool_results": _tool_results(events),
        "events": events,
        "session_id": session_id,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "usage": summary.get("usage"),
    }
