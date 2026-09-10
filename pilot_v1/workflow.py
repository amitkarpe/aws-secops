"""Human decision boundary and compact audit records."""

from __future__ import annotations

import json
from typing import Any, Callable

from .gateway import result_text


GatewayCall = Callable[[str, dict[str, Any]], dict[str, Any]]


def reject_remediation() -> dict[str, Any]:
    return {
        "human_decision": "REJECT",
        "gateway_decision": "NOT_CALLED",
        "tool": "NOT_CALLED",
        "changed": False,
        "verification": "UNCHANGED",
    }


def approve_remediation(environment: str, tool_name: str, call: GatewayCall) -> dict[str, Any]:
    if environment not in {"dev", "prod"}:
        raise ValueError("environment must be dev or synthetic prod")
    response = call(tool_name, {"environment": environment, "approved": True})
    error = response.get("error", {})
    denied = (
        (
            error.get("code") == -32002
            and "Tool Execution Denied" in error.get("message", "")
            and "denied by default" in error.get("message", "")
        )
    )
    if denied:
        return {
            "human_decision": "APPROVE",
            "gateway_decision": "DENY",
            "tool": tool_name,
            "changed": False,
            "verification": "UNCHANGED",
        }
    if response.get("error") or response.get("result", {}).get("isError") is True:
        raise RuntimeError("unexpected Gateway/tool error; not proof of Policy DENY")
    text = result_text(response)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("remediation tool returned invalid JSON") from exc
    if payload.get("result") != "SSH_RULE_REMOVED" or payload.get("changed") is not True:
        raise RuntimeError("remediation tool did not prove the exact change")
    return {
        "human_decision": "APPROVE",
        "gateway_decision": "ALLOW",
        "tool": tool_name,
        "changed": True,
        "verification": payload.get("verification", "UNKNOWN"),
    }
