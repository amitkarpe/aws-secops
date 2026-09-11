"""Three bounded planning tools; none can choose resources or authorize AWS writes."""
from __future__ import annotations

import json
import os
from typing import Literal
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from mcp.server.fastmcp import FastMCP
from pydantic import ConfigDict

from .queries import identity

S3_CONTROL = "s3-bucket-level-public-access-prohibited"
SG_CONTROL = "restricted-ssh"
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
        with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=90) as response:
            raw = response.read(100_001)
        if len(raw) > 100_000:
            raise ValueError("planner response too large")
        value = json.loads(raw)
        if not isinstance(value, dict) or value.get("version") != 1:
            raise ValueError("invalid planner response")
        return value
    except Exception:
        if operation == "prepare":
            raise ValueError("Batch preparation unavailable or rejected. No AWS remediation was authorized; read the plan before retrying.") from None
        raise ValueError("Remediation plan unavailable; no AWS change requested.") from None


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
            prepared.append(with_next_execution(control, call("prepare", control)))
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
            "Each executor must retain its own native Approve/Reject decision. Do not call prepare_remediation_batch for controls listed in skipped."
        ),
    }


server = FastMCP(
    "AWS Compliance Planner",
    instructions=(
        "Server-owned planning for exactly S3 BPA and restricted SSH. Config evidence is intersected with retained owned scope. "
        "The caller never supplies resource IDs, AWS API, account, Region or action. Preparing a batch makes no AWS change and does not approve execution. "
        "Single-family prepare returns one exact executor hint. Fix-all uses prepare_eligible_remediation_batches so completed or ineligible families are skipped server-side."
    ),
)


@server.tool()
def get_remediation_plan(control: Literal["all", "s3-bucket-level-public-access-prohibited", "restricted-ssh"] = "all") -> dict:
    """Read current Config-driven remediation eligibility. No AWS mutation or approval."""
    return call("plan", control)


@server.tool()
def prepare_remediation_batch(control: Literal["s3-bucket-level-public-access-prohibited", "restricted-ssh"]) -> dict:
    """Freeze one exact server-owned batch. On explicit single-family fix intent, invoke returned next_execution."""
    return with_next_execution(control, call("prepare", control))


@server.tool()
def prepare_eligible_remediation_batches() -> dict:
    """Fix-all planner: skip completed/ineligible families and return separate exact ASK executor calls for only eligible families."""
    return prepare_eligible()


for tool in server._tool_manager.list_tools():
    model = tool.fn_metadata.arg_model
    model.model_config = ConfigDict(extra="forbid", strict=True)
    model.model_rebuild(force=True)
    tool.parameters = model.model_json_schema()

if __name__ == "__main__":
    backend()
    server.run(transport="stdio")
