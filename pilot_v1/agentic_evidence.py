"""Evidence-backed agentic SecOps views built only from existing bounded operator reads.

This module does not call AWS or authorize mutation. It turns the current
Config/provider/batch evidence into an operator-facing investigation summary and
a factual decision timeline. Hidden model reasoning is never represented.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

S3_CONTROL = "s3-bucket-level-public-access-prohibited"
BPA_KEYS = {"BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets"}
BPA_TARGET = {key: True for key in BPA_KEYS}
TERMINAL_VERIFIED = {"COMPLETED", "SKIPPED"}
UNCERTAIN_STATES = {"UNKNOWN", "FAILED", "DENIED", "RUNNING", "APPROVED"}


def _control_status(status: dict[str, Any], family: str) -> dict[str, Any]:
    controls = status.get("controls")
    if not isinstance(controls, list):
        raise ValueError("operator status controls missing")
    for item in controls:
        if isinstance(item, dict) and item.get("family") == family:
            return item
    raise ValueError("operator control status missing")


def _bpa(value: object, *, optional: bool = False) -> dict[str, bool] | None:
    if value is None and optional:
        return None
    if not isinstance(value, dict) or set(value) != BPA_KEYS or any(type(value[key]) is not bool for key in BPA_KEYS):
        raise ValueError("unexpected S3 provider evidence")
    return {key: value[key] for key in sorted(BPA_KEYS)}


def _batch_evidence(batch_page: dict[str, Any] | None) -> dict[str, Any]:
    """Summarize the whole durable batch without exposing resource identities.

    `before` is immutable preview/precondition evidence. Only a terminal
    COMPLETED/SKIPPED item's verified `after` value is treated as post-remediation
    provider truth.
    """
    if not batch_page:
        return {
            "mode": "NO_BATCH",
            "items_observed": 0,
            "items_expected": 0,
            "state_counts": {},
            "verified_compliant": 0,
            "preview_noncompliant": 0,
            "message": "No durable batch evidence is available.",
        }
    items = batch_page.get("items")
    total = batch_page.get("total")
    complete = batch_page.get("complete", True)
    summary = batch_page.get("summary") if isinstance(batch_page.get("summary"), dict) else {}
    if not isinstance(items, list) or type(total) is not int or total < 0 or type(complete) is not bool:
        raise ValueError("invalid S3 batch evidence")
    if len(items) > total:
        raise ValueError("S3 batch evidence exceeds total")

    states: Counter[str] = Counter()
    preview_noncompliant = 0
    preview_compliant = 0
    verified_compliant = 0
    verified_noncompliant = 0
    malformed_terminal = 0
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("state"), str):
            raise ValueError("invalid S3 batch item")
        state = item["state"]
        states[state] += 1
        before = _bpa(item.get("before"))
        after = _bpa(item.get("after"), optional=True)
        if state == "PENDING":
            if before == BPA_TARGET:
                preview_compliant += 1
            else:
                preview_noncompliant += 1
        if state in TERMINAL_VERIFIED:
            if after is None:
                malformed_terminal += 1
            elif after == BPA_TARGET:
                verified_compliant += 1
            else:
                verified_noncompliant += 1

    observed = len(items)
    decision = summary.get("decision")
    if not complete or observed != total:
        mode = "PARTIAL_BATCH"
        message = "Only part of the durable batch was observed; no fleet-wide provider conclusion is safe."
    elif total == 0:
        mode = "NO_BATCH"
        message = "The durable batch contains no items."
    elif malformed_terminal or verified_noncompliant:
        mode = "MIXED_OR_INVALID"
        message = "Terminal provider evidence is mixed or incomplete; no global remediation conclusion is safe."
    elif states and set(states) <= TERMINAL_VERIFIED and verified_compliant == total:
        mode = "VERIFIED_COMPLIANT"
        message = "Every observed batch item has terminal provider readback verifying the S3 BPA target."
    elif states and set(states) == {"PENDING"} and decision == "PENDING":
        if preview_noncompliant == total:
            mode = "PREVIEW_NONCOMPLIANT"
            message = "Every observed item has non-compliant preview/precondition evidence; this is not post-remediation provider readback."
        elif preview_compliant == total:
            mode = "PREVIEW_COMPLIANT"
            message = "Every observed item has compliant preview/precondition evidence; this is not post-remediation provider readback."
        else:
            mode = "PREVIEW_MIXED"
            message = "Preview/precondition evidence is mixed; do not classify the fleet from a subset."
    elif any(state in UNCERTAIN_STATES for state in states):
        mode = "INCOMPLETE_OR_UNCERTAIN"
        message = "The batch contains in-progress, failed, denied, or unknown outcomes; no global provider conclusion is safe."
    else:
        mode = "HISTORICAL_OR_UNVERIFIED"
        message = "The saved batch is not a complete current provider-verification set."

    return {
        "mode": mode,
        "items_observed": observed,
        "items_expected": total,
        "state_counts": dict(sorted(states.items())),
        "verified_compliant": verified_compliant,
        "preview_noncompliant": preview_noncompliant,
        "message": message,
    }


def build_s3_investigation(
    plan: dict[str, Any],
    status: dict[str, Any],
    batch_page: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a sanitized investigation summary for the existing S3 family."""
    if plan.get("control") != S3_CONTROL:
        raise ValueError("S3 plan required")
    control = _control_status(status, "s3")
    provider = _batch_evidence(batch_page)

    config_count = int(plan.get("config_noncompliant", 0))
    owned_count = int(plan.get("owned_resources", 0))
    candidate_count = int(plan.get("candidate_owned", 0))
    eligible_count = int(plan.get("eligible_owned", 0))
    unknown_count = int(plan.get("provider_evidence_unknown", owned_count))
    partial = bool(plan.get("partial"))
    ready_to_prepare = bool(plan.get("ready_to_prepare"))

    if min(config_count, owned_count, candidate_count, eligible_count, unknown_count) < 0:
        raise ValueError("negative evidence count")

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
            "source": "Durable S3 batch evidence",
            "fact": "Whole-batch provider/preview evidence summary with resource identities hidden",
            "value": provider,
            "quality": provider["mode"],
        },
    ]

    if partial:
        result = "PARTIAL"
        conclusion = "Investigation is incomplete because AWS Config evidence is partial. Do not prepare remediation from this result."
        recommendation = "Refresh bounded Config evidence before any remediation preparation."
        confidence = "LOW"
        approval = "NOT_READY"
    elif candidate_count == 0:
        result = "NO_CURRENT_OWNED_FINDING"
        conclusion = "No retained owned S3 resource is currently identified by the bounded Config/scope intersection."
        recommendation = "No remediation preparation is recommended from this result."
        confidence = "HIGH"
        approval = "NOT_REQUIRED"
    elif provider["mode"] == "VERIFIED_COMPLIANT":
        result = "PROVIDER_COMPLIANT_CONFIG_LAG"
        conclusion = (
            "AWS Config still identifies the supported S3 control as non-compliant, while complete terminal provider readback verifies the retained batch compliant. "
            "Provider verification is the immediate remediation truth; Config may still be converging."
        )
        recommendation = "Do not remediate again; allow or refresh AWS Config convergence."
        confidence = "HIGH_PROVIDER"
        approval = "NOT_REQUIRED"
    elif provider["mode"] == "PREVIEW_NONCOMPLIANT" and ready_to_prepare:
        result = "ATTENTION"
        conclusion = (
            "The supported S3 control is non-compliant within the retained owned demo scope, and the complete pending batch carries matching non-compliant preview/precondition evidence. "
            "This proves the bounded control/precondition state, not public data exposure, attacker activity, or data sensitivity."
        )
        recommendation = "Use the existing governed remediation path to enable all four bucket-level S3 Block Public Access settings."
        confidence = "HIGH_FOR_BOUNDED_PRECONDITION"
        approval = "REQUIRED_FOR_MUTATION"
    elif provider["mode"] == "PREVIEW_COMPLIANT":
        result = "PRECONDITION_COMPLIANT"
        conclusion = "The saved preview/precondition evidence is compliant even though AWS Config still reports a finding. It is not valid to infer a current mutation need from Config alone."
        recommendation = "Do not prepare a mutation from this evidence; refresh bounded provider/Config evidence."
        confidence = "MEDIUM_PRECONDITION"
        approval = "NOT_REQUIRED"
    else:
        result = "EVIDENCE_INCOMPLETE"
        conclusion = (
            "AWS Config identifies retained owned S3 candidates, but the durable provider evidence is mixed, partial, historical, absent, or otherwise not sufficient for a fleet-wide mutation recommendation."
        )
        recommendation = "Refresh or reconcile bounded provider evidence before deciding whether remediation is required."
        confidence = "LOW_TO_MEDIUM"
        approval = "NOT_READY"

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
        "provider_evidence": provider,
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
    active = bool(batch.get("execution_active"))
    provider = investigation.get("provider_evidence") if isinstance(investigation.get("provider_evidence"), dict) else {}
    provider_mode = provider.get("mode")

    if investigation.get("result") == "PARTIAL":
        finding_status = "PARTIAL"
    elif investigation.get("result") in {"ATTENTION", "PROVIDER_COMPLIANT_CONFIG_LAG", "EVIDENCE_INCOMPLETE", "PRECONDITION_COMPLIANT"}:
        finding_status = "ATTENTION"
    else:
        finding_status = "CLEAR"
    investigation_status = "PARTIAL" if investigation.get("confidence") == "LOW" else ("INCOMPLETE" if investigation.get("result") == "EVIDENCE_INCOMPLETE" else "COMPLETE")
    recommendation_status = "READY" if investigation["mutation"]["approval"] == "REQUIRED_FOR_MUTATION" else ("BLOCKED" if investigation["mutation"]["approval"] == "NOT_READY" else "NO_ACTION")

    if decision == "PENDING":
        human_status, human_summary = "PENDING", "A separate native human decision is still required before execution."
        policy_status, policy_summary = "NOT_CALLED", "Gateway Policy is evaluated only when the exact executor is invoked."
        tool_status, tool_summary = "NOT_CALLED", "No remediation tool call is implied by investigation or planning."
    elif provider_mode == "VERIFIED_COMPLIANT":
        human_status = "APPROVED" if decision == "APPROVE" else "RECORDED"
        human_summary = "The saved batch decision is recorded; identifiers remain hidden by default."
        policy_status, policy_summary = "RECORDED_ELSEWHERE", "Use executor evidence for the exact historical Gateway Policy outcome."
        tool_status, tool_summary = "COMPLETED", "Whole-batch terminal provider evidence verifies the remediation target."
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

    if provider_mode == "VERIFIED_COMPLIANT":
        provider_status = "PASS"
        provider_summary = provider.get("message", "Whole-batch provider verification passed.")
    elif provider_mode in {"PREVIEW_NONCOMPLIANT", "PREVIEW_COMPLIANT", "PREVIEW_MIXED"}:
        provider_status = "PRECONDITION_ONLY"
        provider_summary = provider.get("message", "Preview evidence is not post-remediation provider truth.")
    elif active:
        provider_status = "IN_PROGRESS"
        provider_summary = "Execution is active; wait for terminal provider readback before claiming success."
    elif provider_mode in {"INCOMPLETE_OR_UNCERTAIN", "MIXED_OR_INVALID", "PARTIAL_BATCH"}:
        provider_status = "UNKNOWN"
        provider_summary = provider.get("message", "Provider evidence is not complete enough for a success claim.")
    else:
        provider_status = "NOT_COMPLETE"
        provider_summary = provider.get("message", "No complete current provider-verification claim is available.")

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
        _stage("Investigation", investigation_status, "Bounded whole-batch evidence assembled; identifiers hidden by default.", "operator read path"),
        _stage("Risk / Context", investigation_status, investigation["uncertainty"], "evidence-backed summary"),
        _stage("Recommendation", recommendation_status, investigation["recommendation"], "deterministic control contract"),
        _stage("Policy", policy_status, policy_summary, "AgentCore Gateway Policy"),
        _stage("Human Decision", human_status, human_summary, "native approval record"),
        _stage("Exact Tool", tool_status, tool_summary, "bounded executor"),
        _stage("Provider Readback", provider_status, provider_summary, "durable whole-batch provider evidence"),
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
