"""Single-user Pilot v1 application service."""

from __future__ import annotations

import json
from typing import Any, Callable

from .backlog import FindingBacklog
from .config import PilotConfig
from .findings import normalize_s3, normalize_sg
from .export import to_csv, to_markdown
from .gateway import call_tool, result_text
from .harness import invoke
from .workflow import approve_remediation, reject_remediation


class PilotService:
    def __init__(
        self,
        config: PilotConfig,
        *,
        profile: str = "amit",
        harness_call: Callable[..., dict[str, Any]] = invoke,
        gateway_call: Callable[..., dict[str, Any]] = call_tool,
    ) -> None:
        config.require_harness()
        config.require_gateway()
        if not config.read_tool_name or not config.remediation_tool_name:
            raise ValueError("exact Pilot v1 Gateway tool names are required")
        self.config = config
        self.profile = profile
        self.harness_call = harness_call
        self.gateway_call = gateway_call
        self.findings = FindingBacklog()
        self.state: dict[str, Any] = {
            "stage": "READY",
            "workflow": None,
            "message": "Run the provider check to begin.",
            "finding": None,
            "explanation": None,
            "audit": None,
            "backlog": self.findings.summary(),
        }

    def _refresh_backlog(self) -> None:
        self.state["backlog"] = self.findings.summary()

    def backlog(self) -> dict[str, Any]:
        return self.findings.summary()

    def export_csv(self) -> str:
        return to_csv(self.findings.open_findings())

    def export_markdown(self) -> str:
        return to_markdown(self.findings.open_findings())

    def _call_gateway(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.gateway_call(
            self.config.gateway_url,
            self.config.region,
            self.profile,
            tool_name,
            arguments,
        )

    def _read_finding(self) -> dict[str, Any]:
        response = self._call_gateway(self.config.read_tool_name, {"environment": "dev"})
        if response.get("result", {}).get("isError") is True or response.get("error"):
            raise RuntimeError("provider read was denied or failed")
        try:
            finding = json.loads(result_text(response))
        except json.JSONDecodeError as exc:
            raise RuntimeError("provider read returned invalid JSON") from exc
        if finding.get("status") not in {"COMPLIANT", "NON_COMPLIANT"}:
            raise RuntimeError("provider read returned no compliance decision")
        return finding

    def check(self) -> dict[str, Any]:
        result = self.harness_call(
            self.config,
            "Check the fixed dev demo Security Group for unrestricted TCP/22. "
            "Explain the provider result briefly and end with STATUS: COMPLIANT or STATUS: NON_COMPLIANT.",
        )
        if result["tool_calls"] != 1 or len(result["tool_results"]) != 1:
            raise RuntimeError("Harness did not make exactly one provider read")
        finding = result["tool_results"][0]
        if finding.get("status") not in {"COMPLIANT", "NON_COMPLIANT"}:
            raise RuntimeError("Harness tool result did not contain provider status")
        self.findings.upsert([normalize_sg(finding)])
        self.state = {
            "stage": "FINDING",
            "workflow": "sg",
            "message": "Provider check complete. Choose Reject or Approve.",
            "finding": finding,
            "explanation": result["response"],
            "audit": {
                "provider_finding": finding["status"],
                "ai_recommendation": finding["recommendation"],
                "human_decision": "PENDING",
                "policy_decision": "NOT_CALLED",
                "exact_tool": self.config.read_tool_name,
                "provider_verification": finding["status"],
                "changed": False,
            },
            "backlog": self.findings.summary(),
        }
        return self.state

    def check_s3(self) -> dict[str, Any]:
        if not self.config.s3_tool_name:
            raise RuntimeError("the fixed S3 baseline tool is not configured")
        result = self.harness_call(
            self.config,
            "Check the operator-owned dev S3 bucket allowlist. Report the provider aggregate. "
            "If there are failures, explain only the exceptions; otherwise report the passing counts. "
            "End with STATUS: COMPLIANT or STATUS: NON_COMPLIANT.",
        )
        if result["tool_calls"] != 1 or len(result["tool_results"]) != 1:
            raise RuntimeError("Harness did not make exactly one S3 provider read")
        finding = result["tool_results"][0]
        valid_single = len(finding.get("controls", [])) == 5
        valid_batch = (
            isinstance(finding.get("buckets"), list)
            and 1 <= len(finding["buckets"]) <= 5
            and finding.get("controls_checked") == len(finding["buckets"]) * 5
            and finding.get("pass_count", 0) + finding.get("fail_count", 0)
            == finding.get("controls_checked")
        )
        if finding.get("status") not in {"COMPLIANT", "NON_COMPLIANT"} or not (valid_single or valid_batch):
            raise RuntimeError("Harness S3 result did not contain a valid provider baseline")
        self.findings.upsert(normalize_s3(finding))
        self.state = {
            "stage": "S3_BASELINE",
            "workflow": "s3",
            "message": "Read-only allowlisted S3 assessment complete; no AWS change was made.",
            "finding": finding,
            "explanation": result["response"],
            "audit": {
                "provider_finding": finding["status"],
                "ai_recommendation": finding["recommendation"],
                "human_decision": "NOT_REQUIRED",
                "policy_decision": "ALLOW",
                "exact_tool": self.config.s3_tool_name,
                "provider_verification": finding["status"],
                "changed": False,
            },
            "backlog": self.findings.summary(),
        }
        return self.state

    def reject(self) -> dict[str, Any]:
        if self.state.get("workflow") != "sg":
            raise RuntimeError("run the Security Group provider check first")
        decision = reject_remediation()
        verification = self._read_finding()
        self.state["stage"] = "REJECTED"
        self.state["message"] = "REJECT — no remediation call was made; provider state is unchanged."
        self.state["explanation"] = (
            "The human rejected remediation. Gateway and remediation Lambda were not called; "
            f"the provider still reports {verification['status']}."
        )
        self.state["audit"].update(
            human_decision=decision["human_decision"],
            policy_decision=decision["gateway_decision"],
            exact_tool=decision["tool"],
            provider_verification=verification["status"],
            changed=False,
        )
        self.findings.upsert([normalize_sg(verification)])
        self._refresh_backlog()
        return self.state

    def approve(self, environment: str) -> dict[str, Any]:
        if self.state.get("workflow") != "sg":
            raise RuntimeError("run the Security Group provider check first")

        def gateway(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
            return self._call_gateway(tool_name, arguments)

        decision = approve_remediation(
            environment, self.config.remediation_tool_name, gateway
        )
        verification = self._read_finding()
        denied = decision["gateway_decision"] == "DENY"
        self.state["stage"] = "DENIED" if denied else "COMPLETED"
        self.state["message"] = (
            "DENY — Gateway Policy blocked the synthetic prod request; no remediation occurred."
            if denied
            else "ALLOW — approved remediation completed and AWS provider verification is COMPLIANT."
        )
        self.state["explanation"] = (
            "Gateway Policy denied the synthetic prod context. The remediation Lambda was not "
            f"invoked, and the provider still reports {verification['status']}."
            if denied
            else "The exact public SSH rule was removed after human approval and Gateway Policy "
            f"ALLOW. The independent provider re-read now reports {verification['status']}."
        )
        self.state["finding"] = verification
        self.state["audit"].update(
            human_decision="APPROVE",
            policy_decision=decision["gateway_decision"],
            exact_tool=self.config.remediation_tool_name,
            provider_verification=verification["status"],
            changed=decision["changed"],
        )
        self.findings.upsert([normalize_sg(verification)])
        self._refresh_backlog()
        return self.state
