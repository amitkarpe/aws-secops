"""Evidence-grounded Compliance Agent v1 orchestration."""
from __future__ import annotations

import json
import os
from typing import Any, Callable

from .config_backend import current_evidence
from .harness_client import invoke


def _normalize_request(user_request: str) -> str:
    if not isinstance(user_request, str) or not user_request.strip() or len(user_request) > 4000:
        raise ValueError("user request is invalid")
    return user_request.strip()


def build_prompt(user_request: str, evidence: dict[str, Any]) -> str:
    request = _normalize_request(user_request)
    packet = json.dumps(evidence, separators=(",", ":"), sort_keys=True)
    return f"""USER_REQUEST:\n{request}\n\nAUTHORITATIVE_EVIDENCE_JSON:\n{packet}\n\nADAPTER_RULES:\n- Answer only from AUTHORITATIVE_EVIDENCE_JSON.\n- This Harness/read adapter is read-only and exposes no execution tool. The outer Compliance Agent shell may offer governed remediation through a separate native human-approval path.\n- For a fix/apply/execute request, state that remediation is available only through the separate governed native approval/execution path. Do not claim that the overall Compliance Agent cannot remediate.\n- Account/resource identifiers may be returned only when the evidence packet actually contains them. If they are absent, say they are unavailable from the current evidence. Never invent them.
- If a check has resource_ids_truncated=true, say that only a bounded subset of resource identifiers was supplied when the user asks for all identifiers.\n- For status answers, name all four aliases and both supported controls.\n- AWS Config is asynchronous evidence; do not claim AWS service remediation from Config status alone.\n- For S3 NON_COMPLIANT, state only that the supported S3 control is non-compliant and report the supplied affected-resource count. Do not infer exposure, data sensitivity, provider state, or any other fact.\n- For restricted-ssh NON_COMPLIANT, state only that the supported restricted-SSH control is non-compliant and report the supplied affected-resource count. Do not infer resource relationships, authentication behavior, other network/security controls, exploitability, activity, or any other fact.\n- A no-change remediation plan may state only these exact control-level actions: S3: bring bucket-level Block Public Access into the compliant configuration. Restricted SSH: remove unrestricted SSH ingress and, only if access is still required, replace it with an approved source.\n- Do not mention any AWS service, resource relationship, authentication mechanism, network control, address range, security policy, or hardening/configuration mechanism that is absent from AUTHORITATIVE_EVIDENCE_JSON, even as an example or disclaimer.\n- Do not enumerate or guess how many S3 Block Public Access settings/options exist; say only "bring bucket-level Block Public Access into the compliant configuration".\n- Do not tell the user to re-run AWS Config. State only that Config is asynchronous evidence and AWS service verification is a separate execution-path responsibility.\n- Do not invent resource IDs or unrelated hardening work.\n"""


def answer(
    user_request: str,
    *,
    backend_url: str | None = None,
    harness_arn: str | None = None,
    harness_call: Callable[..., dict[str, Any]] = invoke,
) -> dict[str, Any]:
    request = _normalize_request(user_request)
    backend_url = backend_url or os.environ.get("CONFIG_BACKEND_URL", "http://127.0.0.1:1111")
    harness_arn = harness_arn or os.environ.get("COMPLIANCE_AGENT_V1_HARNESS_ARN", "")
    evidence = current_evidence(backend_url)
    prompt = build_prompt(request, evidence)
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
            "check_count": len(evidence["checks"]),
            "checks": [
                {
                    "account_alias": item["account_alias"],
                    "control": item["control"],
                    "status": item["status"],
                    "affected_resources": item["affected_resources"],
                }
                for item in evidence["checks"]
            ],
            "identifiers_available": evidence["identifiers_available"],
        },
        "mutation": False,
    }
