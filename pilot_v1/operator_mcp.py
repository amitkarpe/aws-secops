"""Bounded planning/investigation tools; none can choose resources or authorize AWS writes."""
from __future__ import annotations

import json
import os
import re
from typing import Literal
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent
from pydantic import ConfigDict

from .agentic_evidence import build_decision_timeline, build_s3_investigation
from .queries import identity
from .ui_cards import (
    render_execution_result,
    render_remediation_preview,
    render_verification_result,
    tool_result,
)

S3_CONTROL = "s3-bucket-level-public-access-prohibited"
SG_CONTROL = "restricted-ssh"
S3_SSL_CONTROL = "s3_ssl"
S3_SSL_DECISION_TOOL = "decide_s3_ssl_reject_only_mcp_aws_compliance_planner"
ORDERED_CONTROLS = (S3_CONTROL, SG_CONTROL)
CONTROLS = {"all", *ORDERED_CONTROLS}
EXECUTOR_BY_CONTROL = {
    S3_CONTROL: "start_batch_execution_mcp_aws_secops_executor",
    SG_CONTROL: "start_sg_batch_execution_mcp_aws_compliance",
}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("backend redirects prohibited")


def backend() -> str:
    value = os.environ.get("SECOPS_OPERATOR_BACKEND_URL", "http://localhost:4444").rstrip("/")
    parsed = urlsplit(value)
    if (parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1"}
            or parsed.port != 4444 or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment):
        raise ValueError("operator planner backend must be fixed loopback port 4444")
    return value


def _request(request: Request, *, timeout: int = 90) -> dict:
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=timeout) as response:
            raw = response.read(100_001)
        if len(raw) > 100_000:
            raise ValueError("operator response too large")
        value = json.loads(raw)
        if not isinstance(value, dict) or value.get("version") != 1:
            raise ValueError("invalid operator response")
        return value
    except Exception as exc:
        raise ValueError("Operator read unavailable or rejected; no AWS change requested.") from exc


def read_path(path: str, query: dict[str, object] | None = None) -> dict:
    if path not in {"/api/operator/status", "/api/operator/plan", "/api/operator/multi-account-plan", "/api/operator/multi-account-execution-preview", "/api/operator/s3-ssl-status", "/api/v1/get_batch"}:
        raise ValueError("unsupported operator read")
    url = backend() + path
    if query:
        url += "?" + urlencode(query)
    return _request(Request(url), timeout=90)


def call(operation: str, control: str) -> dict:
    if control not in CONTROLS or operation not in {"plan", "prepare"}:
        raise ValueError("unsupported planner request")
    base = backend()
    if operation == "plan":
        request = Request(base + "/api/operator/plan?" + urlencode({"control": control}))
    else:
        if control == "all":
            raise ValueError("prepare one exact control at a time")
        request = Request(
            base + "/api/operator/prepare-batch",
            data=json.dumps({"control": control}).encode(),
            headers={"Origin": base, "Content-Type": "application/json"},
        )
    try:
        return _request(request, timeout=90)
    except ValueError:
        if operation == "prepare":
            raise ValueError("Batch preparation unavailable or rejected. No AWS remediation was authorized; read the plan before retrying.") from None
        raise ValueError("Remediation plan unavailable; no AWS change requested.") from None


def multi_account_call(
    operation: str,
    control: str,
    batch_id: str | None = None,
    scope_hash: str | None = None,
    include_accounts: list[str] | None = None,
    exclude_resources: list[str] | None = None,
    exception_reason: str | None = None,
    exception_reference: str | None = None,
    exception_expires_at: str | None = None,
) -> dict:
    if control not in ORDERED_CONTROLS or operation not in {"prepare", "execute"}:
        raise ValueError("unsupported four-account execution request")
    selected = list(include_accounts or [])
    if selected and (len(selected) != len(set(selected)) or not 1 <= len(selected) <= 4
            or any(alias not in {"lab-dev", "lab-poc", "lab-qa", "lab-sec"} for alias in selected)):
        raise ValueError("selected accounts must be 1-4 unique registered LAB aliases")
    canonical = [alias for alias in ("lab-dev", "lab-poc", "lab-qa", "lab-sec") if alias in set(selected)]
    if selected and selected != canonical:
        raise ValueError("selected accounts must use canonical alias order")
    exclusions = list(exclude_resources or [])
    if len(exclusions) > 3 or len(exclusions) != len(set(exclusions)):
        raise ValueError("exact one-time exclusions must be unique and leave at least one target")
    if any(not isinstance(value, str) or not value or len(value) > 255 or any(ch in value for ch in "*?[]") for value in exclusions):
        raise ValueError("invalid exact one-time exclusion")
    base = backend()
    if operation == "prepare":
        if batch_id is not None or scope_hash is not None:
            raise ValueError("prepare does not accept execution identifiers")
        path = "/api/operator/multi-account-execution-plan"
        payload = {"control": control}
        if selected:
            payload["include_accounts"] = selected
        if exclusions:
            payload["exclude_resources"] = exclusions
            payload["exception_reason"] = exception_reason
            if exception_reference:
                payload["exception_reference"] = exception_reference
            if exception_expires_at:
                payload["exception_expires_at"] = exception_expires_at
        elif any(value for value in (exception_reason, exception_reference, exception_expires_at)):
            raise ValueError("exception metadata requires an exact exclusion")
        timeout = 170
    else:
        if exclusions:
            raise ValueError("execute exclusions are frozen server-side during prepare")
        if not isinstance(batch_id, str) or not re.fullmatch(r"[a-f0-9]{20}", batch_id):
            raise ValueError("exact frozen batch id required")
        if not isinstance(scope_hash, str) or not re.fullmatch(r"[a-f0-9]{24}", scope_hash):
            raise ValueError("exact frozen scope hash required")
        path = "/api/operator/multi-account-execute"
        payload = {"control": control, "batch_id": batch_id, "scope_hash": scope_hash}
        timeout = 280
    request = Request(
        base + path,
        data=json.dumps(payload).encode(),
        headers={"Origin": base, "Content-Type": "application/json"},
    )
    try:
        return _request(request, timeout=timeout)
    except ValueError:
        if operation == "execute":
            raise ValueError(
                "Four-account execution unavailable or rejected. Read current status before any retry; do not claim success."
            ) from None
        raise ValueError(
            "Four-account batch preparation unavailable or rejected. No remediation was authorized."
        ) from None


def s3_ssl_reject_prepare() -> dict:
    request = Request(
        backend() + "/api/operator/s3-ssl-reject-prepare", data=b"{}",
        headers={"Origin": backend(), "Content-Type": "application/json"},
    )
    return _request(request, timeout=120)


def s3_ssl_live_status() -> dict:
    return read_path("/api/operator/s3-ssl-status")


def _read_whole_batch(batch_id: str) -> dict:
    """Read every item from one stable batch snapshot without exposing resource IDs."""
    batch_id = identity(batch_id)
    items: list[dict] = []
    offset = 0
    expected_total: int | None = None
    expected_summary: dict | None = None
    while offset <= 1000:
        page = read_path("/api/v1/get_batch", {"batch_id": batch_id, "offset": offset, "limit": 50})
        page_items = page.get("items")
        page_total = page.get("total")
        summary = page.get("summary")
        if not isinstance(page_items, list) or type(page_total) is not int or page_total < 0 or not isinstance(summary, dict):
            raise ValueError("invalid batch page")
        if expected_total is None:
            expected_total = page_total
            expected_summary = summary
        elif page_total != expected_total or summary != expected_summary:
            raise ValueError("batch changed during read")
        items.extend(page_items)
        offset += len(page_items)
        if not page_items or offset >= page_total:
            break
    if expected_total is None or expected_summary is None:
        raise ValueError("batch evidence missing")
    return {
        "version": 1,
        "summary": expected_summary,
        "total": expected_total,
        "items": items,
        "complete": len(items) == expected_total,
    }


def _s3_evidence() -> tuple[dict, dict, dict | None]:
    plan = read_path("/api/operator/plan", {"control": S3_CONTROL})
    status = read_path("/api/operator/status")
    page = None
    batch = plan.get("current_batch")
    if isinstance(batch, dict) and isinstance(batch.get("batch_id"), str):
        page = _read_whole_batch(batch["batch_id"])
    return plan, status, page


def investigate_s3() -> dict:
    plan, status, page = _s3_evidence()
    return build_s3_investigation(plan, status, page)


def decision_timeline() -> dict:
    plan, status, page = _s3_evidence()
    investigation = build_s3_investigation(plan, status, page)
    return build_decision_timeline(investigation, plan, status)


def with_next_execution(control: str, value: dict) -> dict:
    """Add a server-derived executor hint. This does not approve or invoke execution."""
    batch = value.get("batch")
    if not isinstance(batch, dict):
        raise ValueError("prepared batch metadata missing")
    batch_id = batch.get("batch_id")
    approval_hash = batch.get("approval_hash")
    if not isinstance(batch_id, str) or not isinstance(approval_hash, str):
        raise ValueError("prepared batch identifiers missing")
    identity(batch_id)
    identity(approval_hash)
    result = dict(value)
    result["control"] = control
    result["next_execution"] = {
        "tool": EXECUTOR_BY_CONTROL[control],
        "arguments": {"batch_id": batch_id, "approval_hash": approval_hash},
        "native_ask_required": True,
        "instruction": (
            "For an explicit fix/apply/execute request, invoke this exact executor now. "
            "The LibreChat Approve/Reject card appears only after that executor tool call."
        ),
    }
    return result


def _all_plans(value: dict) -> dict[str, dict]:
    plans = value.get("plans")
    if not isinstance(plans, list):
        raise ValueError("all-controls plan missing")
    result: dict[str, dict] = {}
    for item in plans:
        if not isinstance(item, dict):
            raise ValueError("invalid control plan")
        control = item.get("control")
        ready = item.get("ready_to_prepare")
        if control not in ORDERED_CONTROLS or control in result or type(ready) is not bool:
            raise ValueError("invalid all-controls plan")
        result[control] = item
    if set(result) != set(ORDERED_CONTROLS):
        raise ValueError("incomplete all-controls plan")
    return result


def prepare_one(control: str) -> dict:
    if control not in ORDERED_CONTROLS:
        raise ValueError("one exact control required")
    return with_next_execution(control, call("prepare", control))


def prepare_eligible() -> dict:
    """Prepare only currently eligible families for fix-all; skip completed/ineligible families."""
    plans = _all_plans(call("plan", "all"))
    prepared = []
    skipped = []
    for control in ORDERED_CONTROLS:
        plan = plans[control]
        if not plan["ready_to_prepare"]:
            batch = plan.get("current_batch")
            skipped.append({
                "control": control,
                "reason": "not_currently_eligible",
                "current_decision": batch.get("decision") if isinstance(batch, dict) else None,
                "verified": batch.get("verified") if isinstance(batch, dict) else None,
            })
            continue
        try:
            prepared.append(prepare_one(control))
        except ValueError:
            skipped.append({"control": control, "reason": "preparation_rejected"})
    next_executions = [item["next_execution"] for item in prepared]
    return {
        "version": 1,
        "mode": "fix_all",
        "prepared": prepared,
        "skipped": skipped,
        "next_executions": next_executions,
        "native_ask_required": bool(next_executions),
        "instruction": (
            "For the current explicit fix-all request, immediately emit every entry in next_executions as a separate executor tool call in this same assistant turn, before text. "
            "Each executor must retain its own native Approve/Reject decision. Completed or ineligible controls are already skipped server-side."
        ),
    }


server = FastMCP(
    "AWS Compliance Planner",
    instructions=(
        "Server-owned investigation and planning for exactly S3 BPA, restricted SSH, plus live read-only s3_ssl Reject validation. Config evidence is intersected with retained owned scope. "
        "investigate_s3_context and get_s3_decision_timeline are read-only whole-batch evidence views and never expose hidden chain-of-thought. "
        "The caller never supplies resource IDs, AWS API, account, Region or action. Preparing a batch makes no AWS resource change and does not approve execution. "
        "For the primary four-account scope, explicit fix intent must use prepare_multi_account_remediation(control, include_accounts, exclude_resources), then immediately invoke execute_multi_account_remediation(control,batch_id,scope_hash) so LibreChat can show its native Approve/Reject card. If include_accounts is omitted, the server deterministically derives the exact currently NON_COMPLIANT aliases for that control from fresh four-account status; it never defaults a generic fix to already-COMPLIANT aliases. Explicitly supplied aliases remain exact. A successful prepare is not a completed response: emit no assistant text and never ask the user to type Approve, Reject, go, or yes before invoking execute. The native Approve/Reject + Submit card is the only authorization UI. The selected account list is frozen during prepare and never supplied again at execute. Exclusions are resolved deterministically and frozen server-side; execute never accepts a new exclusion list. "
        "Reject means no executor call. S3 and SG approvals remain separate. For s3_ssl status use get_s3_ssl_live_status. For explicitly requested Reject-only validation, call prepare_s3_ssl_reject_only then immediately call its exact next_execution. The native card is Reject-only; the server records the final receipt and checks fresh provider readback. It has no executor path. prepare_remediation(control) is legacy retained single-account behavior only."
    ),
)


@server.tool()
def investigate_s3_context() -> dict:
    """Investigate the current retained S3 BPA finding using bounded Config/provider evidence. Read-only."""
    return investigate_s3()


@server.tool()
def get_s3_decision_timeline() -> dict:
    """Show factual S3 finding-to-verification stages. This is evidence, not model chain-of-thought."""
    return decision_timeline()


@server.tool()
def get_multi_account_remediation_plan(
    control: Literal["all", "s3-bucket-level-public-access-prohibited", "restricted-ssh"] = "all",
) -> dict:
    """Read live four-account Config planning evidence. No AWS mutation or approval."""
    return read_path("/api/operator/multi-account-plan", {"control": control})


@server.tool()
def get_s3_ssl_live_status() -> dict:
    """Read fresh fixed-query S3 TLS posture for the four registered LAB aliases."""
    return s3_ssl_live_status()


@server.tool()
def prepare_multi_account_remediation(
    control: Literal["s3-bucket-level-public-access-prohibited", "restricted-ssh"],
    include_accounts: list[str] | None = None,
    exclude_resources: list[str] | None = None,
    exception_reason: str | None = None,
    exception_reference: str | None = None,
    exception_expires_at: str | None = None,
):
    """Prepare one exact frozen batch for 1-4 exact registered LAB accounts.

    On success, immediately invoke the returned next_execution in the same assistant
    turn so LibreChat displays its native Approve/Reject + Submit card. Never ask
    the user to type Approve/Reject/go/yes between prepare and that native card.

    Omit include_accounts only when the caller did not name aliases; the server then
    derives exactly the aliases currently NON_COMPLIANT for this control from fresh
    four-account status. Explicit aliases remain exact. Accounts not selected are outside
    scope, not exceptions. S3 exclusions must be exact bucket names. Restricted-SSH exclusions must be
    exact Security Group IDs or exact deterministic demo group names. Wildcards,
    ambiguous/unmatched resources and excluding every target fail closed.
    A reason is required for any exclusion; reference and YYYY-MM-DD expiry are
    optional one-time risk-acceptance metadata. Preparation makes no AWS mutation.
    """
    result = multi_account_call(
        "prepare",
        control,
        include_accounts=include_accounts,
        exclude_resources=exclude_resources,
        exception_reason=exception_reason,
        exception_reference=exception_reference,
        exception_expires_at=exception_expires_at,
    )
    result = dict(result)
    result["assistant_transition"] = {
        "mode": "IMMEDIATE_NATIVE_ASK",
        "instruction": (
            "Do not emit assistant text and do not ask the user to type Approve, Reject, go, or yes. "
            "Immediately invoke next_execution with its exact frozen arguments in this same assistant turn. "
            "The LibreChat native Approve/Reject + Submit card is the only mutation authorization UI."
        ),
    }
    next_execution = result["next_execution"]
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=(
                    "TRANSITION_ONLY: remediation scope is frozen. Do not emit assistant text. "
                    "Immediately invoke the executor exactly once with NEXT_EXECUTION_ARGS_JSON="
                    + json.dumps(next_execution["arguments"], separators=(",", ":"), sort_keys=True)
                    + ". Do not substitute any UI resource ID or other identifier for scope_hash. "
                    "If the executor returns DENY or BLOCKED, stop immediately and do not retry."
                ),
            ),
        ],
        structuredContent=result,
    )


@server.tool()
def prepare_s3_ssl_reject_only() -> dict:
    """Prepare one current S3 TLS finding for native Reject-only validation.

    This performs only fixed live reads and freezes one public-safe scope. It
    has no remediation or executor capability. Immediately invoke the exact
    returned decision tool so LibreChat renders its native decision card.
    """
    value = s3_ssl_reject_prepare()
    next_execution = value.get("next_execution")
    if not isinstance(next_execution, dict) or next_execution.get("tool") != S3_SSL_DECISION_TOOL:
        raise ValueError("s3_ssl Reject-only preparation did not return exact decision")
    value["assistant_transition"] = {
        "mode": "IMMEDIATE_NATIVE_ASK_REJECT_ONLY",
        "instruction": "Immediately invoke next_execution. Select Reject only; Approve is blocked.",
    }
    return value


@server.tool()
def decide_s3_ssl_reject_only(control: Literal["s3_ssl"], batch_id: str, scope_hash: str) -> dict:
    """ASK: record one native decision for a frozen Reject-only S3 TLS scope.

    The version-pinned receipt adapter intercepts this exact call. Without the
    adapter this fallback remains blocked and cannot invoke AWS or an executor.
    """
    if control != S3_SSL_CONTROL or not re.fullmatch(r"[a-f0-9]{20}", batch_id) or not re.fullmatch(r"[a-f0-9]{24}", scope_hash):
        raise ValueError("exact s3_ssl Reject-only scope required")
    return {"version": 1, "outcome": "LIVE_EXECUTION_NOT_AUTHORIZED",
            "live_execution_authorized": False, "downstream_dispatches": 0,
            "aws_writes": 0, "message": "Native receipt adapter unavailable; no dispatch."}


@server.tool()
def execute_multi_account_remediation(
    control: Literal["s3-bucket-level-public-access-prohibited", "restricted-ssh"],
    batch_id: str,
    scope_hash: str,
):
    """ASK: Execute one exact frozen selected-account remediation batch after native human approval.

    Reject means this tool is not called. Approve applies only the frozen
    selected account/resource scope. Execution returns quickly with AWS service
    verification pending; verification is a separate read-only step.
    """
    value = multi_account_call("execute", control, batch_id, scope_hash)
    return tool_result(
        value,
        uri=f"ui://aws-secops/remediation-result/{batch_id}",
        html=render_execution_result(value),
        model_text=(
            "The remediation result is rendered in the attached native Ops card. "
            "Render the UI Resource Marker exactly once and do not repeat the result as a Markdown table, "
            "technical list, batch ID, or scope hash. Add only one concise next line: ➡️ Next: Verify latest"
        ),
    )


@server.tool()
def verify_multi_account_remediation(
    control: Literal["s3-bucket-level-public-access-prohibited", "restricted-ssh"],
):
    """Read-only: verify the latest applied remediation directly in AWS service state and show AWS Config evaluation."""
    base = backend()
    request = Request(
        base + "/api/operator/multi-account-verify",
        data=json.dumps({"control": control}).encode(),
        headers={"Origin": base, "Content-Type": "application/json"},
    )
    value = _request(request, timeout=200)
    return tool_result(
        value,
        uri=f"ui://aws-secops/remediation-verification/{control}",
        html=render_verification_result(value),
        model_text=(
            "The latest AWS service verification and AWS Config evaluation are rendered in the attached native Ops card. "
            "Render the UI Resource Marker exactly once and do not repeat the card as a Markdown table or technical list. "
            "Add at most one short plain-English sentence and one concise ➡️ Next line."
        ),
    )


@server.tool()
def get_remediation_plan(control: Literal["all", "s3-bucket-level-public-access-prohibited", "restricted-ssh"] = "all") -> dict:
    """Read current Config-driven remediation eligibility. No AWS mutation or approval."""
    return call("plan", control)


@server.tool()
def prepare_remediation(control: Literal["all", "s3-bucket-level-public-access-prohibited", "restricted-ssh"]) -> dict:
    """Single deterministic preparation entry point for explicit fixes; returns exact native-ASK executor call(s)."""
    if control == "all":
        return prepare_eligible()
    return prepare_one(control)


for tool in server._tool_manager.list_tools():
    model = tool.fn_metadata.arg_model
    model.model_config = ConfigDict(extra="forbid", strict=True)
    model.model_rebuild(force=True)
    tool.parameters = model.model_json_schema()

if __name__ == "__main__":
    backend()
    server.run(transport="stdio")
