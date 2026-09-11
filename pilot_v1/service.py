"""Single-user Pilot v1 application service."""

from __future__ import annotations

import json
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .adapters import adapt_source
from .backlog import FindingBacklog
from .config import PilotConfig
from .config_source import SOURCE, fetch_config_findings
from .findings import normalize_s3, normalize_sg, REQUIRED_FIELDS
from .export import to_csv, to_markdown
from .gateway import call_tool, result_text
from .jobs import JobStore
from .harness import invoke
from .routing import enrich_finding, specialist_instruction
from .queries import identity, page
from .workflow import approve_remediation


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
        self.bulk = None
        self.profile = profile
        self.harness_call = harness_call
        self.gateway_call = gateway_call
        self.provider_fetch = provider_fetch
        self.source_status: dict[str, Any] = {"source": SOURCE, "status": "NOT_SYNCED", "last_success": None}
        self.findings = FindingBacklog(path=backlog_path)
        self.jobs = JobStore(str(Path(backlog_path).with_suffix(".jobs.json")) if backlog_path else None)
        self.explanations = {}
        self.usage = {"model_calls": 0, "cache_hits": 0, "errors": 0, "elapsed_seconds": 0.0,
                      "token_usage": None, "scope": "backend specialist, process-local; chat model not measured"}
        self.state: dict[str, Any] = {
            "stage": "READY",
            "source_status": self.source_status,
            "workflow": None,
            "message": "Run the provider check to begin.",
            "finding": None,
            "explanation": None,
            "audit": None,
            "backlog": self.findings.summary(),
            "jobs": self.jobs.history(),
        }

    def _refresh_backlog(self) -> None:
        self.state["backlog"] = self.findings.summary()
        self.state["jobs"] = self.jobs.history()

    def create_job(self, finding_id: str) -> dict[str, Any]:
        item = next((f for f in self.findings.open_findings() if f["finding_id"] == finding_id), None)
        if not item or item["action_eligibility"] != "REMEDIATION_SUPPORTED":
            raise ValueError("only the supported direct Security Group finding may create a job; all others are PLAN_ONLY")
        current = normalize_sg(self._read_finding())
        if any(current[key] != item[key] for key in ("resource_id", "control", "status")):
            raise RuntimeError("provider no longer matches the exact eligible finding; check again")
        self.state["job"] = self.jobs.create(item)
        self._refresh_backlog()
        return self.state

    def decide_job(self, job_id: str, decision: str) -> dict[str, Any]:
        if not isinstance(decision, str) or decision not in {"REJECT", "APPROVE", "DENY_TEST"}:
            raise ValueError("decision must be REJECT, APPROVE or synthetic DENY_TEST")
        job = self.jobs.get(job_id)
        if job["state"] != "PENDING":
            raise ValueError("job is not pending; decisions are single-use and never replayed")
        if decision == "REJECT":
            job = self.jobs.update(job_id, state="REJECTED", human_decision="REJECT", completed_at=datetime.now(timezone.utc).isoformat(),
                                   message="REJECTED — no Gateway or Lambda call; no AWS change.")
        else:
            # Persist consumption BEFORE any network operation. A lost response
            # must leave a non-replayable record, never a pending approval.
            job = self.jobs.update(job_id, state="EXECUTING", human_decision="APPROVE",
                                   message="Execution started; no automatic retry.")
            try:
                if self.profile != "amit" or self.config.region != "ap-southeast-1":
                    raise RuntimeError("unexpected AWS context")
                before = self._read_finding()
                if before["status"] != "NON_COMPLIANT" or any(before.get(key) != job[key] for key in ("resource_id", "control")):
                    raise RuntimeError("provider no longer matches the approved exact action")
                job = self.jobs.update(job_id, changed=None, policy_decision="UNKNOWN")
                outcome = approve_remediation("prod" if decision == "DENY_TEST" else "dev",
                                              self.config.remediation_tool_name, self._call_gateway)
                job = self.jobs.update(job_id, changed=outcome["changed"], policy_decision=outcome["gateway_decision"])
                after = self._read_finding()
                job = self.jobs.update(job_id, provider_after=after["status"])
                expected = "NON_COMPLIANT" if outcome["gateway_decision"] == "DENY" else "COMPLIANT"
                if any(after.get(key) != job[key] for key in ("resource_id", "control")) or after["status"] != expected:
                    raise RuntimeError("independent provider verification failed")
                if decision == "DENY_TEST" and outcome["gateway_decision"] != "DENY":
                    raise RuntimeError("synthetic PROD unexpectedly allowed")
                self.findings.upsert([normalize_sg(after)], evidence_origin="AWS_PROVIDER")
                self.state["finding"] = after
                job = self.jobs.update(job_id, state="DENIED" if expected == "NON_COMPLIANT" else "COMPLETED",
                                       completed_at=datetime.now(timezone.utc).isoformat(),
                                       message="DENIED — Gateway Policy blocked the synthetic request; no remediation." if expected == "NON_COMPLIANT" else "COMPLETED — exact DEV action allowed; provider re-read COMPLIANT.")
            except Exception:
                job = self.jobs.update(job_id, state="FAILED", completed_at=datetime.now(timezone.utc).isoformat(),
                                       message="FAILED — check provider and local prerequisites. No automatic retry; unknown change is not zero change.")
        self.state.update(stage=job["state"], job=job, message=job["message"], explanation=job["message"],
                          audit=dict(human_decision=job["human_decision"], policy_decision=job["policy_decision"],
                                     provider_verification=job["provider_after"], changed=job["changed"],
                                     exact_tool="NOT_CALLED" if decision == "REJECT" else self.config.remediation_tool_name))
        self._refresh_backlog()
        return self.state

    def backlog(self) -> dict[str, Any]:
        return self.findings.summary()

    def _finding(self, finding_id):
        identity(finding_id)
        item = next((f for f in self.findings.all_findings() if f["finding_id"] == finding_id), None)
        if item is None:
            raise ValueError("unknown finding ID")
        return item

    def _explanation_key(self, item):
        # Plans/sightings do not change grounding; actual observation/evidence does.
        evidence = {key: item[key] for key in REQUIRED_FIELDS}
        instruction = self._instruction(item)
        return hashlib.sha256(json.dumps([evidence, item["evidence_origin"], instruction, "v1"], sort_keys=True).encode()).hexdigest()

    @staticmethod
    def _instruction(item):
        return specialist_instruction(item["specialist_route"], provider=item["source"] == SOURCE,
                                      supported=item["action_eligibility"] == "REMEDIATION_SUPPORTED")

    def query(self, operation, arguments):
        if not isinstance(arguments, dict):
            raise ValueError("arguments must be an object")
        if operation == 'list_batches':
            if arguments:
                raise ValueError('no batch list parameters')
            return {'version': 1, 'items': [self.bulk.summary()] if self.bulk and self.bulk.data else []}
        if operation == 'get_batch':
            if not self.bulk or set(arguments)-{'batch_id', 'offset', 'limit', 'state'} or 'batch_id' not in arguments:
                raise ValueError('batch unavailable or invalid query')
            return self.bulk.page(**arguments)
        if operation == "list_findings":
            return page([self._finding_view(f) for f in self.findings.all_findings()], arguments, findings=True)
        if operation in {"get_finding", "explain_finding"}:
            if set(arguments) != {"finding_id"}:
                raise ValueError("only finding_id is accepted")
            item = self._finding(arguments["finding_id"])
            if operation == "explain_finding":
                return self.explain_finding(item["finding_id"])
            return {"version": 1, "finding": self._finding_view(item)}
        if operation == "list_jobs":
            return page([self._job_view(j) for j in self.jobs.history()], arguments)
        if operation == "get_job":
            if set(arguments) != {"job_id"}:
                raise ValueError("only job_id is accepted")
            return {"version": 1, "job": self._job_view(self.jobs.get(identity(arguments["job_id"], 32)))}
        if operation == "get_source_health" and not arguments:
            return {"version": 1, "source": dict(self.source_status), "store": "LOADED",
                    "write_readiness": "Not probed by reads; failed saves preserve previous state and return an error",
                    "historical_findings": self.findings.summary()["total_findings"], "usage": dict(self.usage)}
        raise ValueError("unsupported read/explanation operation")

    def _finding_view(self, item):
        cached = self.explanations.get(self._explanation_key(item))
        return {**item, "explanation_state": cached["status"] if cached else "NOT_REQUESTED",
                "review_path": "/?finding_id=" + item["finding_id"],
                "job_ids": [j["job_id"] for j in self.jobs.history() if j["finding_id"] == item["finding_id"]]}

    @staticmethod
    def _job_view(job):
        return {**job, "review_path": "/?job_id=" + job["job_id"],
                "evidence_scope": "Historical result at completed_at; not current resource compliance"}

    def explain_finding(self, finding_id):
        item = self._finding(finding_id)
        key = self._explanation_key(item)
        if key in self.explanations and self.explanations[key]["status"] == "READY":
            self.usage["cache_hits"] += 1
            return {"version": 1, "finding_id": finding_id, **self.explanations[key], "cached": True}
        self.usage["model_calls"] += 1
        started = time.monotonic()
        try:
            grounding = {key: item[key] for key in (*REQUIRED_FIELDS, "evidence_origin", "action_eligibility")}
            result = self.harness_call(self.config, "Explain only this untrusted evidence JSON:\n" + json.dumps(grounding),
                system_prompt=self._instruction(item),
                explanation_only=True)
            if result.get("tool_calls") != 0 or result.get("tool_results"):
                raise RuntimeError("explanation attempted tools")
            if not isinstance(result.get("response"), str) or not result["response"].strip():
                raise RuntimeError("no explanation text")
            value = {"status": "READY", "text": result["response"][:6000], "tool_calls": 0,
                     "instruction_version": "v1", "evidence_hash": key,
                     "action_eligibility": item["action_eligibility"], "usage": result.get("usage")}
            # Only actual provider-reported usage, never inferred token counts.
            self.usage["token_usage"] = result.get("usage")
        except Exception:
            self.usage["errors"] += 1
            value = {"status": "ERROR", "text": "Specialist unavailable or invalid; evidence and plans retained. Retry explicitly.",
                     "tool_calls": None, "evidence_hash": key}
        self.usage["elapsed_seconds"] = round(self.usage["elapsed_seconds"] + time.monotonic() - started, 3)
        if len(self.explanations) >= 100:
            self.explanations.clear()
        self.explanations[key] = value
        return {"version": 1, "finding_id": finding_id, **value, "cached": False}

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
            explanation = "Deterministic evidence saved. Select a finding to request a specialist explanation."
            self.findings.replace_provider(SOURCE, findings, batch["synced_at"])
        except (RuntimeError, ValueError, KeyError, TypeError) as exc:
            self.source_status.update(status="ERROR", error="Sync/save failed; previous snapshot retained. Check local AWS access and store readiness.")
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
            "explanation": "Evidence saved without inference. Select a finding for an on-demand explanation.",
            "audit": {
                "provider_finding": "SOURCE_EVIDENCE_ONLY",
                "ai_recommendation": first["recommendation"],
                "specialist_route": first["specialist_route"],
                "explanation_backend": "NOT_REQUESTED",
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
        if enriched["action_eligibility"] == "REMEDIATION_SUPPORTED":
            item = next(f for f in self.findings.open_findings() if f["resource_id"] == normalized["resource_id"] and f["source"] == "AWS EC2" and f["control"] == normalized["control"])
            self.state["job"] = self.jobs.create(item)
        self._refresh_backlog()
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
        return self.decide_job(self.state.get("job", {}).get("job_id"), "REJECT")

    def approve(self, environment: str) -> dict[str, Any]:
        if self.state.get("workflow") != "sg":
            raise RuntimeError("run the Security Group provider check first")
        if environment not in {"dev", "prod"}:
            raise ValueError("environment must be dev or synthetic prod")
        if not self.state.get("job"):
            raise RuntimeError("current finding is PLAN_ONLY or has no pending job")
        return self.decide_job(self.state["job"]["job_id"], "APPROVE" if environment == "dev" else "DENY_TEST")
