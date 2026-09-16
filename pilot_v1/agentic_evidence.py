"""Evidence-backed agentic SecOps views built only from existing bounded operator reads.

This module does not call AWS or authorize mutation. It turns the current
Config/provider/batch evidence into an operator-facing investigation summary and
a factual decision timeline. Hidden model reasoning is never represented.
"""
from __future__ import annotations

from typing import Any

S3_CONTROL = "s3-bucket-level-public-access-prohibited"


def _control_status(status: dict[str, Any], family: str) -> dict[str, Any]:
    controls = status.get("controls")
    if not isinstance(controls, list):
        raise ValueError("operator status controls missing")
    for item in controls:
        if isinstance(item, dict) and item.get("family") == family:
            return item
    raise ValueError("operator control status missing")


def _sample_before(batch_page: dict[str, Any] | None) -> dict[str, bool] | None:
    if not batch_page:
        return None
    items = batch_page.get("items")
    if not isinstance(items, list) or not items:
        return None
    before = items[0].get("before")
    if not isinstance(before, dict):
        return None
    keys = {"BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets"}
    if set(before) != keys or any(type(before[k]) is not bool for k in keys):
        raise ValueError("unexpected S3 provider evidence")
    return {key: before[key] for key in sorted(keys)}


def build_s3_investigation(
    plan: dict[str, Any],
    status: dict[str, Any],
    batch_page: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a sanitized investigation summary for the existing S3 family."""
    if plan.get("control") != S3_CONTROL:
        raise ValueError("S3 plan required")
    control = _control_status(status, "s3")
    before = _sample_before(batch_page)

    config_count = int(plan.get("config_noncompliant", 0))
    owned_count = int(plan.get("owned_resources", 0))
    candidate_count = int(plan.get("candidate_owned", 0))
    eligible_count = int(plan.get("eligible_owned", 0))
    unknown_count = int(plan.get("provider_evidence_unknown", owned_count))
    partial = bool(plan.get("partial"))

    if min(config_count, owned_count, candidate_count, eligible_count, unknown_count) < 0:
        raise ValueError("negative evidence count")

    provider_state = "NOT_SAMPLED"
    if before is not None:
        provider_state = "NON_COMPLIANT" if not all(before.values()) else "COMPLIANT"

    evidence = [
        {
            "source": "AWS Config",
            "fact": "Non-compliant evaluations recorded for the supported S3 control",
            "value": config_count,
            "quality": "PARTIAL" if partial else "RECORDED",
        },
        {
            "source": "Retained owned scope",
            "fact": "Config candidates intersecting the exact retained demo scope",
            "value": candidate_count,
            "quality": "SERVER_DERIVED",
        },
        {
            "source": "Direct provider precondition evidence",
            "fact": "Owned candidates with direct provider evidence matching the remediation precondition",
            "value": eligible_count,
            "quality": "CURRENT_BATCH" if before is not None else "SUMMARY_ONLY",
        },
    ]
    if before is not None:
        evidence.append({
            "source": "S3 provider readback",
            "fact": "One server-selected retained demo resource BPA sample",
            "value": before,
            "quality": provider_state,
        })

    if partial:
        result = "PARTIAL"
        conclusion = "Investigation is incomplete because AWS Config evidence is partial. Do not prepare remediation from this result."
        recommendation = "Refresh bounded Config evidence before any remediation preparation."
        confidence = "LOW"
        approval = "NOT_READY"
    elif candidate_count == 0:
        result = "NO_CURRENT_OWNED_FINDING"
        conclusion = "No retained owned S3 resource is currently identified by the bounded evidence intersection."
        recommendation = "No remediation preparation is recommended from this result."
        confidence = "HIGH"
        approval = "NOT_REQUIRED"
    elif provider_state == "COMPLIANT":
        result = "PROVIDER_COMPLIANT_CONFIG_LAG"
        conclusion = (
            "AWS Config still identifies the supported S3 control as non-compliant, but the sampled direct provider evidence is already compliant. "
            "Provider state is the immediate remediation truth; Config may be converging."
        )
        recommendation = "Do not prepare remediation from provider-compliant evidence; refresh or allow AWS Config to converge."
        confidence = "HIGH_PROVIDER"
        approval = "NOT_REQUIRED"
    else:
        result = "ATTENTION"
        conclusion = (
            "The supported S3 control is non-compliant within the retained owned demo scope. "
            "This proves the control state, not public data exposure, attacker activity, or data sensitivity."
        )
        recommendation = "Enable all four bucket-level S3 Block Public Access settings through the existing governed remediation path."
        confidence = "HIGH_FOR_CONTROL_STATE"
        approval = "REQUIRED_FOR_MUTATION"

    return {
        "version": 1,
        "control": S3_CONTROL,
        "result": result,
        "scope": "retained-owned-demo-only",
        "resource_identity": "hidden-by-default",
        "counts": {
            "config_noncompliant": config_count,
            "owned": owned_count,
            "candidate_owned": candidate_count,
            "eligible_owned": eligible_count,
            "provider_evidence_unknown": unknown_count,
        },
        "evidence": evidence,
        "conclusion": conclusion,
        "recommendation": recommendation,
        "confidence": confidence,
        "uncertainty": "No claim is made about data sensitivity, exploitability, attacker intent, or business impact.",
        "mutation": {
            "performed": False,
            "approval": approval,
            "path": "human approval -> Gateway/Policy -> exact S3 tool -> provider readback",
        },
        "provider_summary": {
            "compliant": control.get("compliant"),
            "noncompliant": control.get("noncompliant"),
            "unknown": control.get("unknown"),
            "evidence_source": control.get("evidence_source"),
        },
    }


def _stage(name: str, status: str, summary: str, source: str) -> dict[str, str]:
    return {"stage": name, "status": status, "summary": summary, "source": source}


def build_decision_timeline(
    investigation: dict[str, Any],
    plan: dict[str, Any],
    status: dict[str, Any],
) -> dict[str, Any]:
    """Build a factual lifecycle view; never expose or fabricate chain-of-thought."""
    if investigation.get("control") != S3_CONTROL or plan.get("control") != S3_CONTROL:
        raise ValueError("S3 evidence required")
    control = _control_status(status, "s3")
    batch = plan.get("current_batch") if isinstance(plan.get("current_batch"), dict) else {}
    decision = batch.get("decision")
    counts = batch.get("counts") if isinstance(batch.get("counts"), dict) else {}
    verified = int(batch.get("verified", 0) or 0)
    total = int(batch.get("total", 0) or 0)
    active = bool(batch.get("execution_active"))

    if investigation.get("result") == "PARTIAL":
        finding_status = "PARTIAL"
    elif investigation.get("result") in {"ATTENTION", "PROVIDER_COMPLIANT_CONFIG_LAG"}:
        finding_status = "ATTENTION"
    else:
        finding_status = "CLEAR"
    investigation_status = "PARTIAL" if investigation.get("confidence") == "LOW" else "COMPLETE"
    recommendation_status = "READY" if investigation["mutation"]["approval"] == "REQUIRED_FOR_MUTATION" else "NO_ACTION"

    if decision == "PENDING":
        human_status, human_summary = "PENDING", "A separate native human decision is still required before execution."
        policy_status, policy_summary = "NOT_CALLED", "Gateway Policy is evaluated only when the exact executor is invoked."
        tool_status, tool_summary = "NOT_CALLED", "No remediation tool call is implied by investigation or planning."
    elif verified and total and verified == total:
        human_status = "APPROVED" if decision == "APPROVE" else "RECORDED"
        human_summary = "The saved batch decision is recorded; identifiers remain hidden by default."
        policy_status, policy_summary = "RECORDED_ELSEWHERE", "Use executor evidence for the exact historical Gateway Policy outcome."
        tool_status, tool_summary = "COMPLETED", "All batch items have direct provider verification."
    elif decision == "APPROVE" or active:
        human_status, human_summary = "APPROVED", "The saved batch indicates approval and execution may be in progress."
        policy_status, policy_summary = "EVALUATED_OR_IN_PROGRESS", "Policy outcome is authoritative in executor/provider evidence, not inferred here."
        tool_status, tool_summary = "IN_PROGRESS", "Exact bounded S3 execution is active or has been dispatched."
    elif decision == "REJECT":
        human_status, human_summary = "REJECTED", "The saved batch was rejected and did not proceed as an approved remediation."
        policy_status, policy_summary = "NOT_INFERRED", "No Gateway Policy result is invented from a rejected batch."
        tool_status, tool_summary = "NOT_CALLED", "No successful mutation is claimed."
    else:
        human_status, human_summary = "NOT_REQUESTED", "No current remediation decision is recorded."
        policy_status, policy_summary = "NOT_CALLED", "No mutation request means no policy execution is required."
        tool_status, tool_summary = "NOT_CALLED", "Investigation remains read-only."

    if verified and total and verified == total:
        provider_status = "PASS"
        provider_summary = f"Direct provider verification recorded for {verified}/{total} batch items."
    elif counts.get("UNKNOWN"):
        provider_status = "UNKNOWN"
        provider_summary = "At least one result is UNKNOWN; this is not success or zero change."
    elif active:
        provider_status = "IN_PROGRESS"
        provider_summary = f"Execution is active; {verified}/{total} items are provider verified."
    else:
        provider_status = "NOT_COMPLETE"
        provider_summary = "No complete current provider-verification claim is available from the batch summary."

    config = control.get("config") if isinstance(control.get("config"), dict) else {}
    config_counts = config.get("counts") if isinstance(config.get("counts"), dict) else {}
    if config.get("partial"):
        compliance_status = "PARTIAL"
        compliance_summary = "AWS Config evidence is partial; convergence cannot be claimed."
    elif config_counts.get("NON_COMPLIANT", 0):
        compliance_status = "NON_COMPLIANT"
        compliance_summary = "AWS Config still records non-compliant evaluations; Config may lag provider state."
    else:
        compliance_status = "NO_CURRENT_NONCOMPLIANT_RETURNED"
        compliance_summary = "No current non-compliant findings were returned by the bounded AWS Config summary."

    stages = [
        _stage("Finding", finding_status, investigation["conclusion"], "AWS Config + retained scope"),
        _stage("Investigation", investigation_status, "Bounded evidence packet assembled; identifiers hidden by default.", "operator read path"),
        _stage("Risk / Context", investigation_status, investigation["uncertainty"], "evidence-backed summary"),
        _stage("Recommendation", recommendation_status, investigation["recommendation"], "deterministic control contract"),
        _stage("Policy", policy_status, policy_summary, "AgentCore Gateway Policy"),
        _stage("Human Decision", human_status, human_summary, "native approval record"),
        _stage("Exact Tool", tool_status, tool_summary, "bounded executor"),
        _stage("Provider Readback", provider_status, provider_summary, "direct AWS provider evidence"),
        _stage("Compliance Result", compliance_status, compliance_summary, "AWS Config"),
    ]
    return {
        "version": 1,
        "control": S3_CONTROL,
        "timeline": stages,
        "identifiers": "hidden-by-default",
        "chain_of_thought": "not-collected-and-not-displayed",
        "message": "This timeline shows observable decisions/evidence only; it is not model chain-of-thought.",
    }
