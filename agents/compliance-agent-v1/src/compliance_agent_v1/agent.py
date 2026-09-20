"""Evidence-grounded Compliance Agent v1 orchestration."""
from __future__ import annotations

import json
import os
from typing import Any, Callable

from .config_backend import current_evidence
from .harness_client import invoke


def build_prompt(user_request: str, evidence: dict[str, Any]) -> str:
    if not isinstance(user_request, str) or not user_request.strip() or len(user_request) > 4000:
        raise ValueError("user request is invalid")
    packet = json.dumps(evidence, separators=(",", ":"), sort_keys=True)
    return f"""USER_REQUEST:\n{user_request.strip()}\n\nAUTHORITATIVE_EVIDENCE_JSON:\n{packet}\n\nADAPTER_RULES:\n- Answer only from AUTHORITATIVE_EVIDENCE_JSON.\n- This v1 adapter is read-only and exposes no execution tool.\n- For a fix/apply/execute request, explain that execution is not available in Compliance Agent v1 and requires the separate governed approval/execution path.\n- Account/resource identifiers may be returned only when the evidence packet actually contains them. If they are absent, say they are unavailable from the current evidence. Never invent them.\n- For status answers, name all four aliases and both supported controls.\n- AWS Config is asynchronous evidence; do not claim provider remediation from Config status alone.\n"""


def answer(
    user_request: str,
    *,
    backend_url: str | None = None,
    harness_arn: str | None = None,
    harness_call: Callable[..., dict[str, Any]] = invoke,
) -> dict[str, Any]:
    backend_url = backend_url or os.environ.get("CONFIG_BACKEND_URL", "http://127.0.0.1:1111")
    harness_arn = harness_arn or os.environ.get("COMPLIANCE_AGENT_V1_HARNESS_ARN", "")
    evidence = current_evidence(backend_url)
    prompt = build_prompt(user_request, evidence)
    result = harness_call(prompt, harness_arn, region=os.environ.get("AWS_REGION", "ap-southeast-1"))
    return {
        "version": 1,
        "agent": "Compliance Agent v1",
        "runtime": "Amazon Bedrock AgentCore Harness",
        "answer": result["answer"],
        "evidence": {
            "source": evidence["source"],
            "fetched_at": evidence["fetched_at"],
            "aliases": evidence["aliases"],
            "controls": evidence["controls"],
            "checks": len(evidence["checks"]),
            "identifiers_available": evidence["identifiers_available"],
        },
        "mutation": False,
    }
