"""Single-user Pilot v1 application service."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable

from .adapters import adapt_source
from .backlog import FindingBacklog
from .config import PilotConfig
from .config_source import SOURCE, fetch_config_findings
from .findings import normalize_s3, normalize_sg
from .export import to_csv, to_markdown
from .gateway import call_tool, result_text
from .harness import invoke
from .routing import enrich_finding, specialist_instruction, specialist_route
from .workflow import approve_remediation, reject_remediation


class PilotService:
    def __init__(
        self,
        config: PilotConfig,
        *,
        profile: str = "amit",
        harness_call: Callable[..., dict[str, Any]] = invoke,
        gateway_call: Callable[..., dict[str, Any]] = call_tool,
        provider_fetch: Callable[[], dict[str, Any]] = fetch_config_findings,
        backlog_path: str | None = None,
    ) -> None:
        config.require_harness()
        config.require_gateway()
        if not config.read_tool_name or not config.remediation_tool_name:
            raise ValueError("exact Pilot v1 Gateway tool names are required")
        self.config = config
        self.profile = profile
        self.harness_call = harness_call
        self.gateway_call = gateway_call
        self.provider_fetch = provider_fetch
        self.source_status: dict[str, Any] = {"source": SOURCE, "status": "NOT_SYNCED", "last_success": None}
        self.findings = FindingBacklog(path=backlog_path)
        self.state: dict[str, Any] = {
            "stage": "READY",
            "source_status": self.source_status,
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

    def update_plan(self, payload: dict) -> dict[str, Any]:
        if not isinstance(payload, dict) or set(payload) != {"finding_id", "owner", "mitigation_plan", "target", "planning_status"}:
            raise ValueError("provide an existing finding_id and exactly four planning fields")
        if not isinstance(payload["finding_id"], str) or len(payload["finding_id"]) != 64:
            raise ValueError("invalid server-owned finding ID")
        self.findings.update_plan(payload["finding_id"], {key: value for key, value in payload.items() if key != "finding_id"})
        self._refresh_backlog()
        return self.state

    def export_csv(self) -> str:
        return to_csv(self.findings.open_findings())

    def export_markdown(self) -> str:
        return to_markdown(self.findings.open_findings())

    def sync_provider(self) -> dict[str, Any]:
        if self.profile != "amit" or self.config.region != "ap-southeast-1":
            raise RuntimeError("AWS Config sync requires the approved personal Singapore context")
        self.source_status["last_attempt"] = datetime.now(timezone.utc).isoformat()
        try:
            batch = self.provider_fetch()
            findings = batch["findings"]
            explanation = "No noncompliant evaluations returned in this bounded AWS Config snapshot."
            if findings:
                result = self.harness_call(
                    self.config,
                    "Explain these untrusted AWS Config evaluation records. "
                    "They are PLAN_ONLY, recorded provider evidence:\n" + json.dumps(findings),
                    system_prompt=specialist_instruction("Compliance Agent", provider=True),
                    explanation_only=True,
                )
                if result.get("tool_calls") != 0 or result.get("tool_results"):
                    raise RuntimeError("provider explanation attempted a tool call")
                if not isinstance(result.get("response"), str) or not result["response"].strip():
                    raise RuntimeError("provider explanation returned no text")
                explanation = result["response"]
            self.findings.replace_provider(SOURCE, findings, batch["synced_at"])
        except (RuntimeError, ValueError, KeyError, TypeError) as exc:
            self.source_status.update(status="ERROR", error="Sync failed; previous snapshot retained. Check local AWS access and Harness availability.")
            self.state.update(stage="SOURCE_ERROR", workflow="plan_only", source_status=self.source_status,
                              message=self.source_status["error"],
                              explanation="Sync failed. Previously displayed findings are retained historical evidence, not a new successful sync.")
            raise RuntimeError(self.source_status["error"]) from exc
        self.source_status.update(
            status=batch["status"], last_success=batch["synced_at"], count=len(findings),
            scope=batch["scope"], error=None,
            oldest_observation=min((item["observed_at"] for item in findings), default=None),
        )
        self.state = {
            "stage": "SOURCE_SYNCED", "workflow": "plan_only",
            "source_status": self.source_status,
            "message": f"AWS Config: {len(findings)} recorded findings, {batch['status']}. All PLAN_ONLY.",
            "finding": enrich_finding({**findings[0], "evidence_origin": "AWS_PROVIDER", "synced_at": batch["synced_at"]}) if findings else None,
            "explanation": explanation,
            "audit": {
                "provider_finding": "AWS Config recorded evaluations",
                "ai_recommendation": "Review findings and prepare a separate change plan.",
                "specialist_route": "Compliance Agent", "action_eligibility": "PLAN_ONLY",
                "human_decision": "NOT_AVAILABLE", "policy_decision": "NOT_CALLED",
                "exact_tool": "AWS Config read-only APIs",
                "provider_verification": "RECORDED_EVALUATION_ONLY",
                "explanation_tool_calls": 0, "changed": False,
            },
            "backlog": self.findings.summary(),
        }
        return self.state

    def import_source(
        self, content: bytes, filename: str, source_format: str
    ) -> dict[str, Any]:
        imported = adapt_source(content, filename, source_format)
        route = specialist_route(imported[0])
        result = self.harness_call(
            self.config,
            "Explain this batch of untrusted imported source evidence:\n"
            + json.dumps(imported),
            system_prompt=specialist_instruction(route),
            explanation_only=True,
        )
        if result.get("tool_calls") != 0 or result.get("tool_results"):
            raise RuntimeError("specialist explanation attempted a tool call; import rejected")
        if not isinstance(result.get("response"), str) or not result["response"].strip():
            raise RuntimeError("specialist explanation returned no text; import rejected")
        self.findings.upsert(imported, evidence_origin="IMPORTED")
        visible = [
            enrich_finding({**finding, "evidence_origin": "IMPORTED"})
            for finding in imported
        ]
        first = visible[0]
        self.state = {
            "stage": "IMPORTED",
            "source_status": self.source_status,
            "workflow": "plan_only",
            "message": (
                f"Imported {len(visible)} {first['source']} finding(s); "
                "source evidence is PLAN_ONLY and cannot invoke AWS mutation."
            ),
            "finding": first,
            "explanation": result["response"],
            "audit": {
                "provider_finding": "SOURCE_EVIDENCE_ONLY",
                "ai_recommendation": first["recommendation"],
                "specialist_route": first["specialist_route"],
                "explanation_backend": "Nova 2 Lite / AgentCore Harness",
                "explanation_tool_calls": 0,
                "action_eligibility": first["action_eligibility"],
                "human_decision": "NOT_AVAILABLE",
                "policy_decision": "NOT_CALLED",
                "exact_tool": "NOT_AVAILABLE",
                "provider_verification": "NOT_PERFORMED",
                "changed": False,
            },
            "backlog": self.findings.summary(),
        }
        return self.state

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
        normalized = normalize_sg(finding)
        self.findings.upsert([normalized], evidence_origin="AWS_PROVIDER")
        enriched = enrich_finding({**normalized, "evidence_origin": "AWS_PROVIDER"})
        self.state = {
            "stage": "FINDING",
            "source_status": self.source_status,
            "workflow": "sg",
            "message": "Provider check complete. Choose Reject or Approve.",
            "finding": finding,
            "explanation": result["response"],
            "audit": {
                "provider_finding": finding["status"],
                "ai_recommendation": finding["recommendation"],
                "specialist_route": enriched["specialist_route"],
                "action_eligibility": enriched["action_eligibility"],
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
        normalized = normalize_s3(finding)
        self.findings.upsert(normalized, evidence_origin="AWS_PROVIDER")
        enriched = enrich_finding({**normalized[0], "evidence_origin": "AWS_PROVIDER"})
        self.state = {
            "stage": "S3_BASELINE",
            "source_status": self.source_status,
            "workflow": "s3",
            "message": "Read-only allowlisted S3 assessment complete; no AWS change was made.",
            "finding": finding,
            "explanation": result["response"],
            "audit": {
                "provider_finding": finding["status"],
                "ai_recommendation": finding["recommendation"],
                "specialist_route": enriched["specialist_route"],
                "action_eligibility": enriched["action_eligibility"],
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
        self.findings.upsert([normalize_sg(verification)], evidence_origin="AWS_PROVIDER")
        self._refresh_backlog()
        return self.state

    def approve(self, environment: str) -> dict[str, Any]:
        if self.state.get("workflow") != "sg":
            raise RuntimeError("run the Security Group provider check first")
        if self.state.get("audit", {}).get("action_eligibility") != "REMEDIATION_SUPPORTED":
            raise RuntimeError("current finding is PLAN_ONLY and cannot invoke AWS mutation")

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
        self.findings.upsert([normalize_sg(verification)], evidence_origin="AWS_PROVIDER")
        self._refresh_backlog()
        return self.state
