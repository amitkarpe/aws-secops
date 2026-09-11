"""Two bounded planning tools; neither can choose resources or authorize AWS writes."""
from __future__ import annotations

import json
import os
from typing import Literal
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from mcp.server.fastmcp import FastMCP
from pydantic import ConfigDict

S3_CONTROL = "s3-bucket-level-public-access-prohibited"
SG_CONTROL = "restricted-ssh"
CONTROLS = {"all", S3_CONTROL, SG_CONTROL}


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


server = FastMCP(
    "AWS Compliance Planner",
    instructions=(
        "Server-owned planning for exactly S3 BPA and restricted SSH. Config evidence is intersected with retained owned scope. "
        "The caller never supplies resource IDs, AWS API, account, Region or action. Preparing a batch makes no AWS change and does not approve execution."
    ),
)


@server.tool()
def get_remediation_plan(control: Literal["all", "s3-bucket-level-public-access-prohibited", "restricted-ssh"] = "all") -> dict:
    """Read current Config-driven remediation eligibility. No AWS mutation or approval."""
    return call("plan", control)


@server.tool()
def prepare_remediation_batch(control: Literal["s3-bucket-level-public-access-prohibited", "restricted-ssh"]) -> dict:
    """Freeze one exact server-owned batch from current eligible evidence. No AWS mutation; native ASK is still required to execute."""
    return call("prepare", control)


for tool in server._tool_manager.list_tools():
    model = tool.fn_metadata.arg_model
    model.model_config = ConfigDict(extra="forbid", strict=True)
    model.model_rebuild(force=True)
    tool.parameters = model.model_json_schema()

if __name__ == "__main__":
    backend()
    server.run(transport="stdio")
