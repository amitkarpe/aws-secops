"""M4A deterministic exceptions and audit evidence over the M3B pilot.

This is a synthetic, server-owned contract.  Exceptions are explicit records,
never compliance outcomes, and the ledger is evidence only: approval continues
to be the inherited exact batch + scope-hash decision boundary.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .csv_bulk_pilot import PILOT_CONTROL, NoopExecutor
from .grouped_selection_pilot import GroupedSelectionPilot
from .scaled_findings import ALIASES

MAX_PAGE_SIZE = 100
_STAMP = "2026-09-22T00:00:00Z"
_RECORD_FIELDS = frozenset({
    "account_alias", "control_key", "resource_id", "owner", "reason",
    "reference", "created_at", "expires_at",
})
_TEXT = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._:/#-]{0,127}\Z")
_TIME = re.compile(r"2026-09-2[0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z\Z")


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _safe(value: str) -> str:
    return f"'{value}" if value.startswith(("=", "+", "-", "@")) else value


class ExceptionRegistry:
    """Append-only exception revisions with strict public-safe input."""

    def __init__(self) -> None:
        self._revisions: list[dict[str, str | int]] = []

    @staticmethod
    def _validate(payload: dict[str, str]) -> None:
        if set(payload) != _RECORD_FIELDS:
            raise ValueError("exception fields must exactly match the public contract")
        if payload["control_key"] != PILOT_CONTROL or payload["account_alias"] not in ALIASES:
            raise ValueError("exception target is unsupported")
        if not payload["resource_id"].startswith("sg-lab-"):
            raise ValueError("exception requires one exact public resource")
        if not all(isinstance(value, str) and _TEXT.fullmatch(value) for value in payload.values()):
            raise ValueError("exception contains an invalid or private value")
        if not _TIME.fullmatch(payload["created_at"]) or not _TIME.fullmatch(payload["expires_at"]):
            raise ValueError("exception timestamps must use the deterministic UTC contract")
        if payload["expires_at"] <= payload["created_at"]:
            raise ValueError("exception expiry must be after creation")

    def create(self, payload: dict[str, str]) -> dict[str, str | int]:
        self._validate(payload)
        exception_id = _digest({"kind": "m4a-exception", **payload})
        if any(row["exception_id"] == exception_id for row in self._revisions):
            raise ValueError("duplicate exception record")
        row: dict[str, str | int] = {
            "version": 1, "exception_id": exception_id, "revision": 1, "status": "ACTIVE", **payload,
        }
        self._revisions.append(row)
        return dict(row)

    def revise(self, exception_id: str, payload: dict[str, str]) -> dict[str, str | int]:
        self._validate(payload)
        current = self._current(exception_id)
        for field in ("account_alias", "control_key", "resource_id", "created_at"):
            if payload[field] != current[field]:
                raise ValueError("exception target and creation time are immutable")
        row: dict[str, str | int] = {
            "version": 1, "exception_id": exception_id, "revision": int(current["revision"]) + 1,
            "status": "ACTIVE", **payload,
        }
        self._revisions.append(row)
        return dict(row)

    def revoke(self, exception_id: str, *, at: str = _STAMP) -> dict[str, str | int]:
        if not _TIME.fullmatch(at):
            raise ValueError("revocation time must use the deterministic UTC contract")
        current = self._current(exception_id)
        row = {**current, "revision": int(current["revision"]) + 1, "status": "REVOKED", "revoked_at": at}
        self._revisions.append(row)
        return dict(row)

    def _current(self, exception_id: str) -> dict[str, str | int]:
        rows = [row for row in self._revisions if row["exception_id"] == exception_id]
        if not rows:
            raise ValueError("unknown exception")
        return dict(max(rows, key=lambda row: int(row["revision"])))

    def current(self, *, as_of: str = _STAMP) -> tuple[dict[str, str | int], ...]:
        if not _TIME.fullmatch(as_of):
            raise ValueError("as_of must use the deterministic UTC contract")
        rows = []
        for exception_id in sorted({str(row["exception_id"]) for row in self._revisions}):
            row = self._current(exception_id)
            if row["status"] == "ACTIVE" and str(row["expires_at"]) <= as_of:
                row["status"] = "EXPIRED"
            rows.append(row)
        return tuple(rows)

    def resolve(self, finding: dict[str, str], *, as_of: str = _STAMP) -> dict[str, Any]:
        target = {key: finding[key] for key in ("account_alias", "control_key", "resource_id")}
        matches = [row for row in self.current(as_of=as_of) if all(row[key] == value for key, value in target.items())]
        active = [row for row in matches if row["status"] == "ACTIVE"]
        if len(active) > 1:
            raise ValueError("conflicting active exceptions for exact finding")
        return {
            "target": target,
            "status": active[0]["status"] if active else (matches[0]["status"] if matches else "NONE"),
            "exception": active[0] if active else (matches[0] if matches else None),
            "all_exception_ids": [str(row["exception_id"]) for row in matches],
            "excludes": bool(active),
        }

    def receipt(self, findings: list[dict[str, str]], *, as_of: str = _STAMP) -> dict[str, Any]:
        resolutions = [self.resolve(finding, as_of=as_of) for finding in findings]
        payload = [{
            "target": item["target"], "status": item["status"],
            "exception_id": item["exception"]["exception_id"] if item["exception"] else None,
            "revision": item["exception"]["revision"] if item["exception"] else None,
        } for item in resolutions]
        return {"version": 1, "as_of": as_of, "exception_digest": _digest(payload),
                "exception_ids": sorted({identifier for item in resolutions for identifier in item["all_exception_ids"]}),
                "read_only": True}

    def summary(self, *, as_of: str = _STAMP) -> dict[str, Any]:
        rows = self.current(as_of=as_of)
        counts = Counter(str(row["status"]) for row in rows)
        expiring = sum(row["status"] == "ACTIVE" and str(row["expires_at"]) <= "2026-09-23T00:00:00Z" for row in rows)
        return {"version": 1, "total": len(rows), "active": counts["ACTIVE"], "expiring_soon": expiring,
                "expired": counts["EXPIRED"], "revoked": counts["REVOKED"], "read_only": True}

    def page(self, *, as_of: str = _STAMP, page: int = 1, limit: int = 25) -> dict[str, Any]:
        if type(page) is not int or page < 1 or type(limit) is not int or not 1 <= limit <= MAX_PAGE_SIZE:
            raise ValueError("exception page is out of bounds")
        rows = [dict(row) for row in self.current(as_of=as_of)]
        start = (page - 1) * limit
        return {"version": 1, "total_count": len(rows), "page": page, "limit": limit,
                "items": rows[start:start + limit], "model_context": "ONE_BOUNDED_EXCEPTION_PAGE", "read_only": True}

    def export_csv(self, *, as_of: str = _STAMP) -> str:
        fields = ("version", "exception_id", "revision", "status", "account_alias", "control_key", "resource_id", "owner", "reason", "reference", "created_at", "expires_at")
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in self.current(as_of=as_of):
            writer.writerow({field: _safe(str(row[field])) for field in fields})
        return output.getvalue()

    def export_receipt(self, *, as_of: str = _STAMP) -> dict[str, Any]:
        content = self.export_csv(as_of=as_of)
        return {"version": 1, "filename": "synthetic-exceptions.csv",
                "row_count": max(0, content.count("\n") - 1),
                "sha256": hashlib.sha256(content.encode()).hexdigest(),
                "content_in_model_context": False, "read_only": True}


class AuditLedger:
    """Hash-chained append-only ledger; its entries never authorize work."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self._events: list[dict[str, Any]] = []
        if path is not None and path.exists():
            loaded = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
            self._verify(loaded)
            self._events = loaded

    @staticmethod
    def _verify(events: list[dict[str, Any]]) -> None:
        prior_hash = "GENESIS"
        for sequence, event in enumerate(events, start=1):
            candidate = dict(event)
            event_hash = candidate.pop("event_hash", None)
            if candidate.get("sequence") != sequence or candidate.get("prior_hash") != prior_hash or event_hash != _digest(candidate):
                raise ValueError("audit ledger integrity check failed")
            prior_hash = str(event_hash)

    def append(self, event_type: str, *, outcome: str, source: str, classification: str = "READ",
               timestamp: str = _STAMP, **bindings: Any) -> dict[str, Any]:
        if not isinstance(event_type, str) or not _TEXT.fullmatch(event_type) or classification not in {"READ", "SYNTHETIC_NOOP"}:
            raise ValueError("invalid public audit event")
        if not _TIME.fullmatch(timestamp):
            raise ValueError("invalid audit timestamp")
        prior_hash = self._events[-1]["event_hash"] if self._events else "GENESIS"
        event = {"sequence": len(self._events) + 1, "event_type": event_type, "timestamp": timestamp,
                 "outcome": outcome, "source": source, "classification": classification,
                 "prior_hash": prior_hash, **bindings}
        event["event_hash"] = _digest(event)
        self._events.append(event)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        return dict(event)

    def page(self, *, page: int = 1, limit: int = 25, batch_id: str | None = None) -> dict[str, Any]:
        if type(page) is not int or page < 1 or type(limit) is not int or not 1 <= limit <= MAX_PAGE_SIZE:
            raise ValueError("audit page is out of bounds")
        rows = [row for row in self._events if batch_id is None or row.get("batch_id") == batch_id]
        start = (page - 1) * limit
        return {"version": 1, "total_count": len(rows), "page": page, "limit": limit,
                "items": [dict(row) for row in rows[start:start + limit]],
                "model_context": "ONE_BOUNDED_AUDIT_PAGE", "read_only": True}

    def timeline(self, batch_id: str) -> dict[str, Any]:
        rows = [row for row in self._events if row.get("batch_id") == batch_id]
        return {"version": 1, "batch_id": batch_id, "event_count": len(rows),
                "event_types": [row["event_type"] for row in rows], "read_only": True}

    def export_jsonl(self) -> str:
        return "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in self._events)

    def export_receipt(self) -> dict[str, Any]:
        content = self.export_jsonl()
        return {"version": 1, "filename": "synthetic-audit-ledger.jsonl", "row_count": len(self._events),
                "sha256": hashlib.sha256(content.encode()).hexdigest(), "content_in_model_context": False, "read_only": True}


class ExceptionAuditPilot(GroupedSelectionPilot):
    """M4A composition: current-truth exceptions + inherited M3 approval/execution."""

    def __init__(self, *args: Any, registry: ExceptionRegistry | None = None, ledger: AuditLedger | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.registry = registry or ExceptionRegistry()
        self.ledger = ledger or AuditLedger()

    def add_exception(self, payload: dict[str, str]) -> dict[str, str | int]:
        row = self.registry.create(payload)
        self.ledger.append("EXCEPTION_CREATED", outcome="RECORDED", source="exception-registry", exception_id=row["exception_id"], revision=row["revision"])
        return row

    def revise_exception(self, exception_id: str, payload: dict[str, str]) -> dict[str, str | int]:
        row = self.registry.revise(exception_id, payload)
        self.ledger.append("EXCEPTION_REVISED", outcome="RECORDED", source="exception-registry", exception_id=exception_id, revision=row["revision"])
        return row

    def revoke_exception(self, exception_id: str) -> dict[str, str | int]:
        row = self.registry.revoke(exception_id)
        self.ledger.append("EXCEPTION_REVOKED", outcome="RECORDED", source="exception-registry", exception_id=exception_id, revision=row["revision"])
        return row

    def add(self, finding_id: str) -> dict[str, Any]:
        result = super().add(finding_id)
        self.ledger.append("MANUAL_SELECTION", outcome="ADDED", source="m3b-selection", finding_id=finding_id, selection_digest=result["selection_digest"])
        return result

    def record_discovery_query(self, *, evidence_digest: str) -> None:
        """Record read-only discovery without turning audit evidence into authority."""
        self.ledger.append("DISCOVERY_QUERY", outcome="RECORDED", source="m2-finding-store", evidence_digest=evidence_digest)

    def record_candidate_intake(self, *, candidate_digest: str) -> None:
        """Record a nominated candidate set; it remains non-authoritative."""
        self.ledger.append("CANDIDATE_INTAKE", outcome="RECORDED", source="m3a-candidate-intake", candidate_digest=candidate_digest)

    def preview_selection(self, *, as_of: str = _STAMP) -> dict[str, Any]:
        evidence = self.store.evidence_receipt()
        selected = self.selection_receipt(include_ids=True)
        rows: list[dict[str, str]] = []
        current_findings: list[dict[str, str]] = []
        for finding_id in selected["finding_ids"]:
            prior = self._selection[finding_id]
            resolved = self.store.resolve_finding_id(finding_id)
            base = {key: prior[key] for key in ("finding_id", "account_alias", "control_key", "resource_id")}
            if resolved is None:
                rows.append({**base, "preview_state": "UNKNOWN", "reason": "NOT_IN_CURRENT_EVIDENCE"})
            elif resolved["control_key"] != PILOT_CONTROL:
                rows.append({**base, "preview_state": "UNSUPPORTED", "reason": "CONTROL_NOT_IN_M3B"})
            elif resolved["config_status"] != "NON_COMPLIANT":
                rows.append({**base, "preview_state": "STALE", "reason": "CURRENT_EVIDENCE_NOT_NON_COMPLIANT"})
            else:
                current_findings.append(resolved)
                resolution = self.registry.resolve(resolved, as_of=as_of)
                if resolution["excludes"]:
                    exception = resolution["exception"]
                    rows.append({**base, "preview_state": "EXCLUDED", "reason": "ACTIVE_MANAGED_EXCEPTION", "exception_id": str(exception["exception_id"])})
                else:
                    rows.append({**base, "preview_state": "ELIGIBLE", "reason": "CURRENT_EVIDENCE_MATCH"})
        rows.sort(key=lambda row: row["finding_id"])
        receipt = self.registry.receipt(current_findings, as_of=as_of)
        eligible = [row for row in rows if row["preview_state"] == "ELIGIBLE"]
        excluded = [row for row in rows if row["preview_state"] == "EXCLUDED"]
        scope = {"control": PILOT_CONTROL,
                 "eligible": [{key: row[key] for key in ("finding_id", "account_alias", "resource_id")} for row in eligible],
                 "exclusions": [{key: row[key] for key in ("finding_id", "account_alias", "resource_id")} for row in excluded],
                 "selection_digest": selected["selection_digest"], "evidence_version": evidence["version"],
                 "evidence_digest": evidence["evidence_digest"], "selected_accounts": sorted({row["account_alias"] for row in eligible}),
                 "exception_as_of": as_of, "exception_digest": receipt["exception_digest"], "exception_ids": receipt["exception_ids"]}
        self.ledger.append("EXCEPTION_RESOLUTION", outcome="RESOLVED", source="exception-registry", selection_digest=selected["selection_digest"], exception_digest=receipt["exception_digest"], exception_ids=receipt["exception_ids"])
        preview = self._freeze_preview(rows, scope)
        preview["selected_count"] = selected["selected_count"]
        preview["exception_digest"] = receipt["exception_digest"]
        if preview["batch_id"]:
            self.ledger.append("PREVIEW_FROZEN", outcome="FROZEN", source="m3a-freezer", batch_id=preview["batch_id"], scope_hash=preview["scope_hash"], exception_digest=receipt["exception_digest"], classification="READ")
        return preview

    def _current_exception_digest(self, batch: dict[str, Any]) -> str:
        findings = []
        for row in batch["rows"]:
            resolved = self.store.resolve_finding_id(row["finding_id"])
            if resolved is not None:
                findings.append(resolved)
        return self.registry.receipt(findings, as_of=batch["scope"]["exception_as_of"])["exception_digest"]

    def decide(self, batch_id: str, scope_hash: str, decision: str) -> dict[str, Any]:
        try:
            batch = self._batch(batch_id, scope_hash)
            if self._current_exception_digest(batch) != batch["scope"]["exception_digest"]:
                raise ValueError("exception state changed; re-prepare the candidate scope")
            result = super().decide(batch_id, scope_hash, decision)
        except ValueError as exc:
            self.ledger.append("REPLAY_BLOCKED" if "terminal" in str(exc) else "DECISION_BLOCKED", outcome="BLOCKED", source="native-approval", batch_id=batch_id, scope_hash=scope_hash)
            raise
        self.ledger.append("NATIVE_APPROVAL_DECISION", outcome=result["decision"], source="native-approval", batch_id=batch_id, scope_hash=scope_hash, classification="READ")
        return result

    def execute_approved(self, batch_id: str, scope_hash: str, executor: NoopExecutor | None = None) -> dict[str, Any]:
        try:
            result = super().execute_approved(batch_id, scope_hash, executor)
        except ValueError as exc:
            self.ledger.append("REPLAY_BLOCKED" if "terminal" in str(exc) else "EXECUTION_BLOCKED", outcome="BLOCKED", source="synthetic-noop", batch_id=batch_id, scope_hash=scope_hash)
            raise
        self.ledger.append("EXECUTION_DISPATCH", outcome=result["decision"], source="synthetic-noop", batch_id=batch_id, scope_hash=scope_hash, classification="SYNTHETIC_NOOP")
        self.ledger.append("EXECUTION_RESULT", outcome=result["decision"], source="synthetic-noop", batch_id=batch_id, scope_hash=scope_hash, classification="SYNTHETIC_NOOP")
        return result

    def record_provider_verification(self, batch_id: str, scope_hash: str, outcome: str) -> None:
        self._batch(batch_id, scope_hash)
        self.ledger.append("PROVIDER_VERIFICATION", outcome=outcome, source="provider-readback", batch_id=batch_id, scope_hash=scope_hash)

    def record_config_convergence(self, batch_id: str, scope_hash: str, outcome: str) -> None:
        self._batch(batch_id, scope_hash)
        self.ledger.append("CONFIG_CONVERGENCE", outcome=outcome, source="config-evaluation", batch_id=batch_id, scope_hash=scope_hash)

    def exception_view(self, **kwargs: Any) -> dict[str, Any]:
        page = self.registry.page(**kwargs)
        for row in page["items"]:
            row["target_state"] = "CURRENT" if self.store.resolve_candidate(
                str(row["account_alias"]), str(row["control_key"]), str(row["resource_id"])
            ) else "STALE_TARGET"
        return {"summary": self.registry.summary(as_of=kwargs.get("as_of", _STAMP)),
                "page": page, "read_only": True}

    def audit_view(self, **kwargs: Any) -> dict[str, Any]:
        return self.ledger.page(**kwargs)

    def exception_export_receipt(self, *, as_of: str = _STAMP) -> dict[str, Any]:
        self.ledger.append("EXPORT_GENERATION", outcome="EXCEPTIONS_EXPORTED", source="exception-export")
        return self.registry.export_receipt(as_of=as_of)

    def audit_export_receipt(self) -> dict[str, Any]:
        self.ledger.append("EXPORT_GENERATION", outcome="AUDIT_EXPORTED", source="audit-export")
        return self.ledger.export_receipt()


__all__ = ["AuditLedger", "ExceptionAuditPilot", "ExceptionRegistry", "MAX_PAGE_SIZE"]
