"""Simple authenticated-frontend operator homepage over the retained S3 worker.

Served by the same loopback service already behind ops.astromedicomp.org. The
homepage can deliberately re-arm exact demo resources after a confirmation, but
normal remediation authorization remains in LibreChat native ASK + Gateway Policy.
"""
from __future__ import annotations

import argparse
import hashlib
from http.server import HTTPServer
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .bulk import BulkStore
from .bulk_gateway import GovernedS3Provider
from .bulk_server import BulkHandler, BulkService
from .control_catalog import get_control, public_catalog
from .demo_prepare import S3_NONCOMPLIANT, count_s3, require_resettable, reset_s3
from .operator_protocol import ConfirmationGate
from .org_config_overview import read_status as read_four_account_status, remediation_plan as four_account_plan
from .codebuild_execution import BuildError, run as run_four_account_build

S3_CONTROL = "s3-bucket-level-public-access-prohibited"
SG_CONTROL = "restricted-ssh"
APPROVAL_TTL_SECONDS = 1800

LATEST_ACCEPTANCE = {
    "date": "2026-09-18",
    "scope": "four-account GitHub OIDC acceptance proof",
    "aliases": ["lab-dev", "lab-poc", "lab-qa", "lab-sec"],
    "controls": {
        S3_CONTROL: {
            "reject_writes": 0, "approve_mutations": 4,
            "provider_verified": True, "config": "COMPLIANT x4",
            "rerun": "ALREADY_COMPLIANT / 0 writes",
        },
        SG_CONTROL: {
            "reject_writes": 0, "approve_mutations": 4,
            "provider_verified": True, "config": "COMPLIANT x4",
            "rerun": "ALREADY_COMPLIANT / 0 writes",
        },
    },
    "note": "Acceptance evidence only; live retained-resource cards below show current runtime state.",
    "scp_change": False,
    "config_auto_remediation": False,
}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("internal redirects prohibited")


class OperatorService(BulkService):
    def __init__(
        self,
        bulk: BulkStore,
        sg_origin: str = "http://localhost:4455",
        execution_state: Path | None = None,
    ):
        super().__init__(bulk)
        if sg_origin != "http://localhost:4455":
            raise ValueError("SG backend must use the fixed loopback service")
        self.sg_origin = sg_origin
        self.gate = ConfirmationGate()
        self.execution_state = execution_state or Path("/tmp/aws-secops-four-account-execution.json")

    def _sg(self, path: str, payload: dict | None = None) -> dict:
        url = self.sg_origin + path
        data = None if payload is None else json.dumps(payload).encode()
        headers = {"Origin": self.sg_origin, "Content-Type": "application/json"}
        request = Request(url, data=data, headers=headers)
        with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=75) as response:
            raw = response.read(200_001)
        if len(raw) > 200_000:
            raise RuntimeError("SG response too large")
        value = json.loads(raw)
        if not isinstance(value, dict) or value.get("version") != 1:
            raise RuntimeError("invalid SG response")
        return value

    def _s3_fingerprint(self) -> str:
        from .bulk import digest
        summary = self.bulk.summary()
        return digest({
            "family": "s3", "batch_id": summary.get("batch_id"), "decision": summary.get("decision"),
            "counts": summary.get("counts", {}), "manifest_hash": self.bulk.provider.context.get("manifest_hash"),
        })

    def _s3_pending_demo_ready(self, summary: dict, provider: dict | None = None) -> bool:
        if not self.bulk.data or summary.get("decision") != "PENDING":
            return False
        total = len(self.bulk.provider.resources)
        counts = summary.get("counts", {})
        if counts.get("PENDING") != total or any(counts.get(x, 0) for x in ("APPROVED", "RUNNING", "UNKNOWN")):
            return False
        evidence = self.bulk.data.get("manifest", {}).get("resources", [])
        if len(evidence) != total or not all(x.get("before") == S3_NONCOMPLIANT for x in evidence):
            return False
        provider = provider or count_s3(self.bulk.provider)
        return (
            provider.get("total") == total
            and provider.get("noncompliant") == total
            and provider.get("compliant") == 0
            and provider.get("unknown") == 0
        )

    def _config_control(self, control: str) -> dict:
        summary = self._sg("/api/v1/get_config_summary")
        for item in summary.get("controls", []):
            if item.get("control") == control:
                return item
        raise RuntimeError("Config control unavailable")

    def _config_noncompliant(self, control: str) -> tuple[set[str], bool]:
        found: set[str] = set()
        partial = False
        offset = 0
        total = None
        while offset < 250:
            query = urlencode({"control": control, "status": "NON_COMPLIANT", "offset": offset, "limit": 50})
            page = self._sg("/api/v1/list_config_findings?" + query)
            total = int(page.get("total", 0))
            partial = partial or bool(page.get("partial"))
            items = page.get("items", [])
            if not isinstance(items, list) or len(items) > 50:
                raise RuntimeError("invalid Config finding page")
            found.update(str(x["resource_id"]) for x in items)
            offset += len(items)
            if not items or offset >= total:
                break
        if total is not None and len(found) < min(total, 250):
            partial = True
        return found, partial

    @staticmethod
    def _unavailable_control(family: str, title: str, action: str, message: str) -> dict:
        return {
            "version": 1, "family": family, "title": title,
            "resource_count": None, "compliant": None, "noncompliant": None, "unknown": None,
            "last_verification_time": None, "batch": None, "config": None,
            "status_available": False, "config_available": False,
            "status_error": message, "config_error": "AWS Config status unavailable",
            "action": action,
        }

    def s3_status(self) -> dict:
        summary = self.bulk.summary()
        counts = summary.get("counts", {}) if summary.get("batch_id") else {}
        total = len(self.bulk.provider.resources)
        compliant = int(summary.get("verified", 0)) if summary.get("batch_id") else 0
        noncompliant = int(counts.get("PENDING", 0) + counts.get("APPROVED", 0) + counts.get("DENIED", 0))
        unknown = max(0, total - compliant - noncompliant)
        # Old journals do not have event timestamps. Do not manufacture one from
        # batch creation or file mtime: neither proves when AWS was verified.
        evidence_time = summary.get("last_verification_time")
        config = None
        config_available = True
        config_error = None
        try:
            config = self._config_control(S3_CONTROL)
        except Exception:
            config_available = False
            config_error = "AWS Config status unavailable"
        return {
            "version": 1, "family": "s3", "title": "S3 Block Public Access",
            "resource_count": total, "compliant": compliant, "noncompliant": noncompliant,
            "unknown": unknown, "last_verification_time": evidence_time,
            "evidence_source": "Saved S3 batch readback (not a fresh scan)",
            "batch": summary, "config": config,
            "status_available": True, "config_available": config_available,
            "status_error": None, "config_error": config_error,
            "action": "enable all four bucket-level Block Public Access settings",
        }

    def multi_account_status(self) -> dict:
        return read_four_account_status()

    def multi_account_plan(self, control: str) -> dict:
        return four_account_plan(control)

    def _execution_cache(self) -> dict:
        try:
            value = json.loads(self.execution_state.read_text())
        except FileNotFoundError:
            return {"version": 1, "plans": {}}
        if not isinstance(value, dict) or value.get("version") != 1 or not isinstance(value.get("plans"), dict):
            raise RuntimeError("invalid four-account execution cache")
        return value

    def _save_execution_cache(self, value: dict) -> None:
        self.execution_state.parent.mkdir(parents=True, exist_ok=True)
        temp = self.execution_state.with_suffix(self.execution_state.suffix + ".new")
        temp.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")))
        os.chmod(temp, 0o600)
        os.replace(temp, self.execution_state)

    @staticmethod
    def _normalize_exclusions(values: object) -> list[str]:
        if values is None:
            return []
        if not isinstance(values, list) or len(values) > 3 or len(values) != len(set(values)):
            raise ValueError("exact exclusions must be a unique list of up to three resources")
        for value in values:
            if (not isinstance(value, str) or not value or len(value) > 255
                    or any(ch in value for ch in "*?[]")):
                raise ValueError("invalid exact exclusion resource")
        return values

    @staticmethod
    def _normalize_exception_metadata(
        exclusions: list[str],
        reason: object = None,
        reference: object = None,
        expires_at: object = None,
    ) -> dict:
        if not exclusions:
            if any(value not in {None, ""} for value in (reason, reference, expires_at)):
                raise ValueError("exception metadata requires at least one exclusion")
            return {"reason": None, "reference": None, "expires_at": None, "requested_at": None}
        if not isinstance(reason, str) or not 3 <= len(reason.strip()) <= 200:
            raise ValueError("one-time exclusion reason is required")
        reason = reason.strip()
        if reference in {None, ""}:
            reference = None
        elif (not isinstance(reference, str) or len(reference) > 64
              or not all(ch.isalnum() or ch in "._:/-" for ch in reference)):
            raise ValueError("invalid exception reference")
        if expires_at in {None, ""}:
            expires_at = None
        elif not isinstance(expires_at, str):
            raise ValueError("invalid exception expiry")
        else:
            try:
                time.strptime(expires_at, "%Y-%m-%d")
            except ValueError as exc:
                raise ValueError("exception expiry must be YYYY-MM-DD") from exc
            if expires_at < time.strftime("%Y-%m-%d", time.gmtime()):
                raise ValueError("exception expiry is already past")
        return {
            "reason": reason,
            "reference": reference,
            "expires_at": expires_at,
            "requested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    @staticmethod
    def _normalize_selected_accounts(values: object = None) -> list[str]:
        allowed = ["lab-dev", "lab-poc", "lab-qa", "lab-sec"]
        if values is None:
            return allowed
        if not isinstance(values, list) or not 1 <= len(values) <= 4:
            raise ValueError("selected accounts must be a list of 1-4 approved aliases")
        if len(values) != len(set(values)) or any(not isinstance(x, str) or x not in allowed for x in values):
            raise ValueError("selected accounts must be unique approved aliases")
        canonical = [alias for alias in allowed if alias in set(values)]
        if values != canonical:
            raise ValueError("selected accounts must use canonical alias order")
        return canonical

    def prepare_multi_account_execution(
        self,
        control: str,
        include_accounts: object = None,
        exclude_resources: object = None,
        exception_reason: object = None,
        exception_reference: object = None,
        exception_expires_at: object = None,
    ) -> dict:
        if control not in {S3_CONTROL, SG_CONTROL}:
            raise ValueError("one exact supported control required")
        current = self.multi_account_status()
        rows = current.get("accounts", [])
        by_alias = {row.get("alias"): row for row in rows if isinstance(row, dict)}
        allowed_accounts = ["lab-dev", "lab-poc", "lab-qa", "lab-sec"]
        states = {
            alias: by_alias.get(alias, {}).get("controls", {}).get(control)
            for alias in allowed_accounts
        }
        if any(state not in {"COMPLIANT", "NON_COMPLIANT"} for state in states.values()):
            raise ValueError("complete current four-account compliance state required before preparation")
        if include_accounts is None:
            selected_accounts = [
                alias for alias in allowed_accounts if states[alias] == "NON_COMPLIANT"
            ]
            if not selected_accounts:
                raise ValueError("no current NON_COMPLIANT accounts for requested control")
        else:
            selected_accounts = self._normalize_selected_accounts(include_accounts)
        unselected_accounts = [alias for alias in allowed_accounts if alias not in selected_accounts]
        exclusions = self._normalize_exclusions(exclude_resources)
        exception = self._normalize_exception_metadata(
            exclusions, exception_reason, exception_reference, exception_expires_at
        )
        if any(states[alias] != "NON_COMPLIANT" for alias in selected_accounts):
            raise ValueError("selected account scope must currently be NON_COMPLIANT")
        result = run_four_account_build(
            "plan", control, exclusions=exclusions, include_accounts=selected_accounts
        )
        pending_aliases = result.get("pending_aliases")
        excluded_aliases = result.get("excluded_aliases", [])
        if result.get("decision") != "PLAN":
            raise ValueError("frozen plan is not eligible")
        if (not isinstance(pending_aliases, list) or not isinstance(excluded_aliases, list)
                or len(pending_aliases) + len(excluded_aliases) != len(selected_accounts)
                or set(pending_aliases) & set(excluded_aliases)
                or set(pending_aliases) | set(excluded_aliases) != set(selected_accounts)):
            raise ValueError("frozen plan scope does not match selected registered aliases")
        if result.get("excluded_count") != len(exclusions):
            raise ValueError("frozen plan exclusion count mismatch")
        batch_id = result.get("batch_id")
        if not isinstance(batch_id, str):
            raise RuntimeError("frozen batch id missing")
        scope_payload = {
            "control": control,
            "batch_id": batch_id,
            "selected_accounts": selected_accounts,
            "unselected_accounts": unselected_accounts,
            "pending_aliases": pending_aliases,
            "excluded_aliases": excluded_aliases,
            "exclude_resources": exclusions,
            "exception": exception,
        }
        scope_hash = hashlib.sha256(
            json.dumps(scope_payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:24]
        cache = self._execution_cache()
        cache["plans"][control] = {
            "control": control,
            "batch_id": batch_id,
            "selected_accounts": selected_accounts,
            "unselected_accounts": unselected_accounts,
            "pending_aliases": pending_aliases,
            "excluded_aliases": excluded_aliases,
            "exclude_resources": exclusions,
            "exception": exception,
            "scope_hash": scope_hash,
            "created_at": int(time.time()),
            "execution_state": "PENDING_APPROVAL",
        }
        self._save_execution_cache(cache)
        return {
            "version": 1,
            "scope": "four-account-live-config",
            "control": control,
            "batch_id": batch_id,
            "selected_accounts": selected_accounts,
            "unselected_accounts": unselected_accounts,
            "pending_aliases": pending_aliases,
            "excluded_aliases": excluded_aliases,
            "excluded_resources": exclusions,
            "exception_source": "one-time-user-exclusion" if exclusions else None,
            "exception": exception if exclusions else None,
            "scope_hash": scope_hash,
            "native_ask_required": True,
            "next_execution": {
                "tool": "execute_multi_account_remediation_mcp_aws_compliance_planner",
                "arguments": {"control": control, "batch_id": batch_id, "scope_hash": scope_hash},
            },
            "message": (
                f"Exact batch frozen for {len(selected_accounts)} selected account(s): "
                f"{len(pending_aliases)} included, {len(exclusions)} excluded. "
                "Invoke the native-ASK executor for this exact scope."
            ),
            "mutation": False,
            "account_ids": "hidden-by-default",
            "resource_identifiers": "hidden-by-default",
        }

    def multi_account_execution_preview(self, control: str) -> dict:
        if control not in {S3_CONTROL, SG_CONTROL}:
            raise ValueError("one exact supported control required")
        plan = self._execution_cache().get("plans", {}).get(control)
        if not isinstance(plan, dict):
            raise ValueError("no prepared four-account execution")
        age = int(time.time()) - int(plan.get("created_at", 0))
        if age < 0 or age > APPROVAL_TTL_SECONDS:
            raise ValueError("prepared four-account execution expired")
        return {
            "version": 1,
            "scope": "four-account-live-config",
            "control": control,
            "batch_id": plan.get("batch_id"),
            "selected_accounts": plan.get("selected_accounts", ["lab-dev", "lab-poc", "lab-qa", "lab-sec"]),
            "unselected_accounts": plan.get("unselected_accounts", []),
            "pending_aliases": plan.get("pending_aliases"),
            "excluded_aliases": plan.get("excluded_aliases", []),
            "excluded_resources": plan.get("exclude_resources", []),
            "exception_source": "one-time-user-exclusion" if plan.get("exclude_resources") else None,
            "exception": plan.get("exception") if plan.get("exclude_resources") else None,
            "scope_hash": plan.get("scope_hash"),
            "execution_state": plan.get("execution_state", "PENDING_APPROVAL"),
            "age_seconds": age,
            "account_ids": "hidden-by-default",
            "resource_identifiers": "hidden-by-default",
        }

    def _clear_multi_account_execution(self, control: str) -> None:
        cache = self._execution_cache()
        cache.get("plans", {}).pop(control, None)
        self._save_execution_cache(cache)

    def _mark_multi_account_execution(self, control: str, state: str) -> None:
        cache = self._execution_cache()
        plan = cache.get("plans", {}).get(control)
        if not isinstance(plan, dict):
            raise ValueError("no prepared four-account execution")
        plan["execution_state"] = state
        plan["execution_updated_at"] = int(time.time())
        self._save_execution_cache(cache)

    def _reconcile_multi_account_execution(self, preview: dict, exclusions: list[str]) -> dict:
        control = preview["control"]
        batch_id = preview["batch_id"]
        expected_included = list(preview.get("pending_aliases") or [])
        expected_excluded = list(preview.get("excluded_aliases") or [])
        result = run_four_account_build(
            "verify",
            control,
            batch_id,
            exclusions=exclusions,
            include_accounts=preview.get("selected_accounts"),
            timeout=180,
        )
        if result.get("batch_id") != batch_id:
            raise RuntimeError("provider reconciliation batch scope changed")
        if result.get("excluded_aliases", []) != expected_excluded:
            raise RuntimeError("excluded resource changed; operator review required")
        pending = result.get("pending_aliases", [])
        if not isinstance(pending, list):
            raise RuntimeError("provider reconciliation returned invalid included scope")
        if pending == expected_included:
            return {"state": "NOT_STARTED", "result": result}
        if not pending:
            return {"state": "RECOVERED_VERIFIED", "result": result}
        raise RuntimeError("partial provider state after execution; no automatic retry")

    def _multi_account_execution_response(
        self,
        preview: dict,
        exclusions: list[str],
        result: dict,
        *,
        recovered: bool,
    ) -> dict:
        expected_included = list(preview.get("pending_aliases") or [])
        decision = "RECOVERED_VERIFIED" if recovered else result.get("decision")
        mutation_count = None if recovered else result.get("mutation_count")
        verified_count = len(expected_included)
        return {
            "version": 1,
            "scope": "four-account-live-config",
            "control": preview.get("control"),
            "batch_id": preview.get("batch_id"),
            "decision": decision,
            "mutation_count": mutation_count,
            "verified_included_count": verified_count,
            "provider_verified": True,
            "recovered_after_timeout": recovered,
            "included_aliases": expected_included,
            "excluded_aliases": preview.get("excluded_aliases", []),
            "excluded_resources": exclusions,
            "excluded_resources_unchanged": True,
            "exception_source": "one-time-user-exclusion" if exclusions else None,
            "exception": preview.get("exception") if exclusions else None,
            "scope_hash": preview.get("scope_hash"),
            "config_states": result.get("config"),
            "execution_backend": (
                "Provider reconciliation via AWS CodeBuild read-only plan"
                if recovered else result.get("execution_backend")
            ),
            "account_ids": "hidden-by-default",
            "resource_identifiers": "hidden-by-default",
            "message": (
                f"{'Recovered verified completion' if recovered else 'Provider readback completed'} "
                f"for {verified_count} included target(s); {len(exclusions)} excluded target(s) "
                "were verified unchanged. AWS Config convergence is independent and may still be pending."
            ),
        }

    def execute_multi_account(self, control: str, batch_id: str, scope_hash: str) -> dict:
        if control not in {S3_CONTROL, SG_CONTROL}:
            raise ValueError("one exact supported control required")
        plan = self._execution_cache().get("plans", {}).get(control)
        if not isinstance(plan, dict):
            raise ValueError("no prepared four-account execution")
        age = int(time.time()) - int(plan.get("created_at", 0))
        if age < 0:
            raise ValueError("prepared four-account execution has invalid age")
        expired = age > APPROVAL_TTL_SECONDS
        preview = {
            "version": 1,
            "scope": "four-account-live-config",
            "control": control,
            "batch_id": plan.get("batch_id"),
            "selected_accounts": plan.get("selected_accounts", ["lab-dev", "lab-poc", "lab-qa", "lab-sec"]),
            "unselected_accounts": plan.get("unselected_accounts", []),
            "pending_aliases": plan.get("pending_aliases"),
            "excluded_aliases": plan.get("excluded_aliases", []),
            "excluded_resources": plan.get("exclude_resources", []),
            "exception": plan.get("exception") if plan.get("exclude_resources") else None,
            "scope_hash": plan.get("scope_hash"),
            "execution_state": plan.get("execution_state", "PENDING_APPROVAL"),
            "age_seconds": age,
        }
        if (
            preview.get("batch_id") != batch_id
            or not isinstance(scope_hash, str)
            or not re.fullmatch(r"[a-f0-9]{24}", scope_hash)
            or preview.get("scope_hash") != scope_hash
        ):
            raise ValueError("submitted batch does not match frozen plan")

        exclusions = self._normalize_exclusions(preview.get("excluded_resources"))
        execution_state = preview.get("execution_state", "PENDING_APPROVAL")

        current = self.multi_account_status()
        rows = current.get("accounts", [])
        selected_accounts = list(preview.get("selected_accounts") or [])
        by_alias = {row.get("alias"): row for row in rows if isinstance(row, dict)}
        all_noncompliant = bool(selected_accounts) and all(
            alias in by_alias
            and by_alias[alias].get("controls", {}).get(control) == "NON_COMPLIANT"
            for alias in selected_accounts
        )

        # Any retry after dispatch, or any changed Config scope from an older
        # pre-state-tracking batch, reconciles provider state before deciding
        # whether another write is safe.
        if expired or execution_state == "EXECUTING" or not all_noncompliant:
            reconciliation = self._reconcile_multi_account_execution(preview, exclusions)
            if reconciliation["state"] == "RECOVERED_VERIFIED":
                response = self._multi_account_execution_response(
                    preview, exclusions, reconciliation["result"], recovered=True
                )
                self._clear_multi_account_execution(control)
                return response
            if expired:
                raise RuntimeError(
                    "expired frozen batch did not reconcile to verified completion; no execution was dispatched"
                )
            if execution_state == "EXECUTING":
                raise RuntimeError(
                    "previous remediation outcome is still unresolved; no second execution was dispatched"
                )
            raise ValueError("live Config scope changed; prepare a new exact batch")

        self._mark_multi_account_execution(control, "EXECUTING")
        try:
            result = run_four_account_build(
                "execute",
                control,
                batch_id,
                exclusions=exclusions,
                include_accounts=selected_accounts,
                timeout=180,
            )
        except BuildError:
            # Keep EXECUTING. A later call must reconcile provider state and
            # must never blindly dispatch a second mutation.
            raise

        if result.get("decision") not in {"APPROVE", "ALREADY_COMPLIANT"}:
            raise RuntimeError("unexpected selective execution result")
        expected_mutations = len(preview.get("pending_aliases") or [])
        if result.get("decision") == "APPROVE" and result.get("mutation_count") != expected_mutations:
            raise RuntimeError("AWS change count did not match exact selected scope")
        if result.get("excluded_aliases", []) != preview.get("excluded_aliases", []):
            raise RuntimeError("excluded scope changed during execution")

        self._mark_multi_account_execution(control, "APPLIED_PENDING_VERIFICATION")
        return {
            "version": 1,
            "scope": "selected-lab-accounts",
            "control": control,
            "batch_id": batch_id,
            "decision": "APPLIED_PENDING_VERIFICATION",
            "selected_accounts": selected_accounts,
            "unselected_accounts": preview.get("unselected_accounts", []),
            "included_aliases": preview.get("pending_aliases", []),
            "excluded_aliases": preview.get("excluded_aliases", []),
            "excluded_resources": exclusions,
            "scope_hash": scope_hash,
            "aws_change_applied": True,
            "aws_service_verification": "PENDING",
            "aws_config_evaluation": "PENDING",
            "mutation_count": result.get("mutation_count"),
            "account_ids": "hidden-by-default",
            "resource_identifiers": "hidden-by-default",
            "message": (
                f"AWS change applied to {expected_mutations} selected account(s). "
                "AWS service verification is pending. AWS Config evaluation may update later."
            ),
        }

    def verify_multi_account_execution(self, control: str) -> dict:
        if control not in {S3_CONTROL, SG_CONTROL}:
            raise ValueError("one exact supported control required")
        plan = self._execution_cache().get("plans", {}).get(control)
        if not isinstance(plan, dict):
            raise ValueError("no recent remediation batch available to verify")
        if plan.get("execution_state") not in {"APPLIED_PENDING_VERIFICATION", "EXECUTING", "VERIFIED"}:
            raise ValueError("latest remediation has not been applied")
        selected_accounts = self._normalize_selected_accounts(plan.get("selected_accounts"))
        exclusions = self._normalize_exclusions(plan.get("exclude_resources"))
        result = run_four_account_build(
            "verify",
            control,
            plan.get("batch_id"),
            exclusions=exclusions,
            include_accounts=selected_accounts,
            timeout=180,
        )
        verified = result.get("aws_service_verification") == "VERIFIED"
        if verified:
            self._mark_multi_account_execution(control, "VERIFIED")
        return {
            "version": 1,
            "scope": "selected-lab-accounts",
            "control": control,
            "selected_accounts": selected_accounts,
            "unselected_accounts": plan.get("unselected_accounts", []),
            "included_aliases": result.get("included_aliases", []),
            "excluded_aliases": result.get("excluded_aliases", []),
            "aws_service_verification": result.get("aws_service_verification", "NOT_VERIFIED"),
            "aws_config_evaluation": result.get("config", {}),
            "verified": verified,
            "account_ids": "hidden-by-default",
            "resource_identifiers": "hidden-by-default",
            "message": (
                "AWS service verification complete."
                if verified else
                "AWS service verification is not complete; no automatic remediation retry was dispatched."
            ),
        }


    def status(self) -> dict:
        degraded = []
        try:
            multi_account = self.multi_account_status()
        except Exception:
            multi_account = {
                "version": 1,
                "scope": "four-account-live-config",
                "source": "AWS Config organization aggregator",
                "accounts": [],
                "controls": [S3_CONTROL, SG_CONTROL],
                "account_ids": "hidden-by-default",
                "resource_identifiers": "not-collected",
                "mutation": False,
                "available": False,
                "message": "Live four-account Config evidence is temporarily unavailable.",
            }
            degraded.append("four-account Config overview unavailable")
        try:
            s3 = self.s3_status()
        except Exception:
            s3 = self._unavailable_control(
                "s3", "S3 Block Public Access",
                "enable all four bucket-level Block Public Access settings",
                "S3 provider/batch status unavailable",
            )
        try:
            sg = self._sg("/api/operator/sg-status")
        except Exception:
            sg = self._unavailable_control(
                "sg", "Security Group restricted SSH",
                "remove only TCP/22 ingress from 0.0.0.0/0",
                "Security Group provider/batch status unavailable",
            )
        for control in (s3, sg):
            if control.get("status_available") is False:
                degraded.append(control.get("status_error") or f"{control.get('title', control.get('family'))} status unavailable")
            if control.get("config_available") is False:
                degraded.append(control.get("config_error") or f"{control.get('title', control.get('family'))} AWS Config unavailable")
            elif isinstance(control.get("config"), dict) and control["config"].get("partial"):
                degraded.append(f"{control.get('title', control.get('family'))} AWS Config evidence is partial")
        return {
            "version": 1, "agent_url": "https://sec.astromedicomp.org/",
            "controls": [s3, sg],
            "multi_account": multi_account,
            "acceptance": LATEST_ACCEPTANCE,
            "catalog": public_catalog(),
            "degraded": bool(degraded), "degraded_sources": degraded,
            "message": ("Partial status: " + "; ".join(degraded) + ". Provider/batch truth is shown where available."
                        if degraded else "Provider verification is immediate truth; AWS Config convergence may lag."),
        }

    def prepare_preview(self, family: str) -> dict:
        if family == "sg":
            return self._sg("/api/operator/sg-prepare-preview", {})
        if family != "s3":
            raise ValueError("unsupported family")
        with self.bulk.lock:
            summary = self.bulk.summary()
            provider = count_s3(self.bulk.provider)
            already_ready = self._s3_pending_demo_ready(summary, provider)
            if not already_ready:
                require_resettable(summary)
            fingerprint = self._s3_fingerprint()
            token = self.gate.issue("s3", fingerprint)
            return {
                "version": 1, "family": "s3", "confirmation_token": token,
                "resource_count": len(self.bulk.provider.resources),
                "action": ("reuse the existing verified pending demo batch; no AWS change"
                           if already_ready else
                           "set BlockPublicAcls=false only; preserve other BPA flags, empty buckets, ACL-disabled ownership and no bucket policy"),
                "warning": ("The S3 demo is already re-armed. Confirmation reuses the existing pending batch with zero AWS changes."
                            if already_ready else
                            "This intentionally makes these demo buckets non-compliant. Unrelated resources are not changed."),
                "already_ready": already_ready,
            }

    def prepare_demo(self, family: str, token: str) -> dict:
        if family == "sg":
            return self._sg("/api/operator/sg-prepare", {"confirmation_token": token})
        if family != "s3":
            raise ValueError("unsupported family")
        with self.bulk.lock:
            summary = self.bulk.summary()
            provider = count_s3(self.bulk.provider)
            already_ready = self._s3_pending_demo_ready(summary, provider)
            if not already_ready:
                require_resettable(summary)
            fingerprint = self._s3_fingerprint()
            self.gate.consume(token, "s3", fingerprint)
            if already_ready:
                return {
                    "version": 1, "status": "DEMO_READY", "family": "s3",
                    "resource_count": provider["total"], "compliant": 0,
                    "noncompliant": provider["noncompliant"], "unknown": 0,
                    "changed": 0, "batch_id": summary["batch_id"], "reused": True,
                    "message": f"DEMO READY — {provider['total']} S3 buckets already verified non-compliant. Existing pending batch reused with 0 changes.",
                }
            try:
                reset = reset_s3(self.bulk.provider)
                provider = count_s3(self.bulk.provider)
                if (provider["noncompliant"] != provider["total"]
                        or provider["compliant"] or provider["unknown"]):
                    return {"version": 1, "status": "FAILED", "family": "s3", **provider,
                            "message": "S3 re-arm did not fully verify the known non-compliant starting state."}
                rolled_over = self.bulk.rollover_terminal_history()
                batch = self.bulk.preview(renew=not rolled_over)
                before = [x.get("before") for x in self.bulk.data["manifest"]["resources"]]
                verified_noncompliant = sum(x == S3_NONCOMPLIANT for x in before)
            except Exception:
                provider = count_s3(self.bulk.provider)
                return {"version": 1, "status": "FAILED", "family": "s3", **provider,
                        "message": "Prepare interrupted or failed. Exact provider counts are shown; do not retry blindly."}
            if (verified_noncompliant != len(before) or batch.get("decision") != "PENDING"
                    or batch.get("counts", {}).get("PENDING") != len(before)):
                return {"version": 1, "status": "FAILED", "family": "s3",
                        "resource_count": len(before), "noncompliant": verified_noncompliant,
                        "message": "Provider reset or fresh preview did not fully verify ready."}
            return {"version": 1, "status": "DEMO_READY", "family": "s3",
                    "resource_count": len(before), "compliant": 0, "noncompliant": len(before), "unknown": 0,
                    "changed": reset["changed"], "batch_id": batch["batch_id"],
                    "message": f"DEMO READY — {len(before)} S3 buckets verified non-compliant. A fresh batch is ready. Open AWS Compliance Agent in LibreChat."}

    def s3_plan(self) -> dict:
        config_noncompliant, partial = self._config_noncompliant(S3_CONTROL)
        owned = set(self.bulk.provider.resources)
        batch = self.bulk.summary()
        direct_noncompliant: set[str] = set()
        direct_unknown = len(owned)
        if self.bulk.data and batch.get("decision") == "PENDING":
            evidence = self.bulk.data["manifest"]["resources"]
            direct_noncompliant = {x["resource"] for x in evidence if x.get("before") == S3_NONCOMPLIANT}
            direct_unknown = len(owned - direct_noncompliant)
        candidates = owned & config_noncompliant
        eligible = candidates & direct_noncompliant
        catalog = get_control(S3_CONTROL)
        return {
            "version": 1, "control": S3_CONTROL, **catalog,
            "config_noncompliant": len(config_noncompliant), "owned_resources": len(owned),
            "candidate_owned": len(candidates), "eligible_owned": len(eligible),
            "provider_evidence_unknown": direct_unknown,
            "excluded": len(config_noncompliant - owned), "partial": partial,
            "ready_to_prepare": not partial and bool(owned) and candidates == owned,
            "current_batch": batch,
            "message": ("Config identifies candidate owned resources. Existing immutable preview evidence supplies direct provider eligibility; "
                        "if absent, explicit batch preparation performs the bounded provider precondition read before any approval."),
        }

    def plan(self, control: str) -> dict:
        if control == "all":
            return {"version": 1, "control": "all", "plans": [self.s3_plan(), self._sg("/api/operator/sg-plan?control=restricted-ssh")],
                    "message": "Plan all; S3 and Security Group still require separate immutable batches and separate native approvals."}
        if control == S3_CONTROL:
            return self.s3_plan()
        if control == SG_CONTROL:
            return self._sg("/api/operator/sg-plan?control=restricted-ssh")
        raise ValueError("unsupported control")

    def prepare_batch(self, control: str) -> dict:
        if control == SG_CONTROL:
            return self._sg("/api/operator/sg-prepare-batch", {"control": SG_CONTROL})
        if control != S3_CONTROL:
            raise ValueError("one exact control required")
        plan = self.s3_plan()
        if not plan["ready_to_prepare"]:
            raise ValueError("Config evidence is not ready for the complete owned S3 batch")
        with self.bulk.lock:
            summary = self.bulk.summary()
            if self.bulk.data and summary.get("decision") == "PENDING":
                before = self.bulk.data["manifest"]["resources"]
                if all(x.get("before") == S3_NONCOMPLIANT for x in before):
                    return {"version": 1, "prepared": True, "family": "s3", "batch": summary, "reused": True}
                raise ValueError("current S3 preview does not match the exact remediation precondition")
            if self.bulk.data:
                require_resettable(summary)
                batch = self.bulk.preview(renew=True)
            else:
                batch = self.bulk.preview()
            before = self.bulk.data["manifest"]["resources"]
            if not all(x.get("before") == S3_NONCOMPLIANT for x in before):
                self.bulk.decide(batch["batch_id"], batch["approval_hash"], "REJECT")
                raise ValueError("direct S3 provider precondition does not match Config candidate scope")
            return {"version": 1, "prepared": True, "family": "s3", "batch": batch, "reused": False}


class OperatorHandler(BulkHandler):
    service: OperatorService
    operator_page = Path(__file__).with_name("static").joinpath("operator.html")

    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        if parsed.path == "/":
            if not self._local_host():
                self._json(403, {"error": "unexpected local Host"}); return
            body = self.operator_page.read_bytes()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        if parsed.path == "/api/operator/status":
            if not self._local_host():
                self._json(403, {"error": "unexpected local Host"}); return
            try: self._json(200, self.service.status())
            except Exception: self._json(503, {"error": "operator status unavailable"})
            return
        if parsed.path == "/api/operator/multi-account-plan":
            if not self._local_host():
                self._json(403, {"error": "unexpected local Host"}); return
            try:
                query = parse_qs(parsed.query, strict_parsing=True)
                if set(query) != {"control"} or len(query["control"]) != 1:
                    raise ValueError("one control required")
                self._json(200, self.service.multi_account_plan(query["control"][0]))
            except ValueError: self._json(400, {"error": "invalid four-account plan request"})
            except Exception: self._json(503, {"error": "four-account plan unavailable"})
            return
        if parsed.path == "/api/operator/multi-account-execution-preview":
            if not self._local_host():
                self._json(403, {"error": "unexpected local Host"}); return
            try:
                query = parse_qs(parsed.query, strict_parsing=True)
                if set(query) != {"control"} or len(query["control"]) != 1:
                    raise ValueError("one control required")
                self._json(200, self.service.multi_account_execution_preview(query["control"][0]))
            except ValueError: self._json(400, {"error": "invalid or stale four-account execution preview"})
            except Exception: self._json(503, {"error": "four-account execution preview unavailable"})
            return
        if parsed.path == "/api/operator/plan":
            if not self._local_host():
                self._json(403, {"error": "unexpected local Host"}); return
            try:
                query = parse_qs(parsed.query, strict_parsing=True)
                if set(query) != {"control"} or len(query["control"]) != 1:
                    raise ValueError("one control required")
                self._json(200, self.service.plan(query["control"][0]))
            except ValueError: self._json(400, {"error": "invalid remediation plan request"})
            except Exception: self._json(503, {"error": "remediation plan unavailable"})
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path not in {
            "/api/operator/prepare-preview",
            "/api/operator/prepare",
            "/api/operator/prepare-batch",
            "/api/operator/multi-account-execution-plan",
            "/api/operator/multi-account-execute",
            "/api/operator/multi-account-verify",
        }:
            super().do_POST(); return
        if not self._local_host() or not self._same_loopback_origin():
            self._json(403, {"error": "same loopback origin required"}); return
        if self.headers.get_content_type() != "application/json":
            self._json(415, {"error": "application/json required"}); return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= 4096:
                raise ValueError("invalid payload")
            data = json.loads(self.rfile.read(length))
            if self.path == "/api/operator/prepare-preview" and set(data) == {"family"}:
                result = self.service.prepare_preview(data["family"])
            elif self.path == "/api/operator/prepare" and set(data) == {"family", "confirmation_token"}:
                result = self.service.prepare_demo(data["family"], data["confirmation_token"])
            elif self.path == "/api/operator/prepare-batch" and set(data) == {"control"}:
                result = self.service.prepare_batch(data["control"])
            elif (self.path == "/api/operator/multi-account-execution-plan"
                  and set(data).issubset({
                      "control", "include_accounts", "exclude_resources", "exception_reason",
                      "exception_reference", "exception_expires_at",
                  })
                  and "control" in data):
                result = self.service.prepare_multi_account_execution(
                    data["control"],
                    data.get("include_accounts"),
                    data.get("exclude_resources"),
                    data.get("exception_reason"),
                    data.get("exception_reference"),
                    data.get("exception_expires_at"),
                )
            elif self.path == "/api/operator/multi-account-execute" and set(data) == {"control", "batch_id", "scope_hash"}:
                result = self.service.execute_multi_account(
                    data["control"], data["batch_id"], data["scope_hash"]
                )
            elif self.path == "/api/operator/multi-account-verify" and set(data) == {"control"}:
                result = self.service.verify_multi_account_execution(data["control"])
            else:
                raise ValueError("invalid operator request")
            self._json(200, result)
        except (ValueError, RuntimeError):
            self._json(400, {"error": "operator request rejected; no automatic retry"})
        except Exception:
            self._json(503, {"error": "operator operation unavailable; inspect saved state before retry"})


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--gateway-state", type=Path, required=True)
    p.add_argument("--state", type=Path, required=True)
    p.add_argument("--port", type=int, default=4444)
    args = p.parse_args()
    if not 1024 <= args.port <= 65535:
        p.error("invalid local port")
    provider = GovernedS3Provider(args.manifest, args.gateway_state)
    store = BulkStore(args.state, provider)
    OperatorHandler.service = OperatorService(
        store,
        os.environ.get("SECOPS_SG_BACKEND_URL", "http://localhost:4455"),
        args.state.with_name("four-account-execution-plan.json"),
    )
    try:
        with HTTPServer(("127.0.0.1", args.port), OperatorHandler) as server:
            print(f"BULK_OPERATOR=http://localhost:{args.port}/ OPERATOR_HOME=ON MODE={provider.context['mode']}", flush=True)
            server.serve_forever()
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
