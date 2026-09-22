"""M3A synthetic CSV candidate-scope pilot.

CSV rows nominate candidates only. The current server-owned finding store is the
only evidence source and is re-resolved before a frozen native-approval batch
can exist. This module deliberately contains no AWS client or model-exposed
execution tool.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable

from .scaled_findings import MAX_PAGE_SIZE, ScaledFindingStore

CANDIDATE_FIELDS = ("account_alias", "control_key", "resource_id")
RESULT_FIELDS = (
    "account_alias", "control_key", "resource_id", "finding_id",
    "preview_state", "execution_state", "verification_state",
)
MAX_CANDIDATE_BYTES = 128_000
MAX_CANDIDATE_ROWS = 1_000
MAX_REJECTED_PAGE_SIZE = 100
PILOT_CONTROL = "restricted_ssh"
RESULT_FILENAME = "synthetic-bulk-results.csv"
PREVIEW_STATES = frozenset({"ELIGIBLE", "DUPLICATE", "STALE", "UNKNOWN", "UNSUPPORTED", "EXCLUDED"})


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()


def _csv_safe(value: str) -> str:
    return f"'{value}" if value.startswith(("=", "+", "-", "@")) else value


@dataclass(frozen=True)
class Candidate:
    account_alias: str
    control_key: str
    resource_id: str

    def key(self) -> tuple[str, str, str]:
        return (self.account_alias, self.control_key, self.resource_id)

    def public(self) -> dict[str, str]:
        return dict(zip(CANDIDATE_FIELDS, self.key(), strict=True))


def parse_candidate_csv(content: bytes) -> tuple[Candidate, ...]:
    """Strictly parse a bounded, public-safe candidate CSV without interpreting it."""
    if not isinstance(content, bytes) or not content or len(content) > MAX_CANDIDATE_BYTES:
        raise ValueError("candidate CSV must be non-empty and within the byte limit")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("candidate CSV must be UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None or tuple(reader.fieldnames) != CANDIDATE_FIELDS:
        raise ValueError("candidate CSV columns must exactly match the public contract")
    candidates: list[Candidate] = []
    for raw in reader:
        if None in raw or set(raw) != set(CANDIDATE_FIELDS):
            raise ValueError("candidate CSV row is malformed")
        values = []
        for field in CANDIDATE_FIELDS:
            value = raw[field]
            if not isinstance(value, str):
                raise ValueError("candidate CSV row is malformed")
            value = value.strip()
            if not value or len(value) > 128 or value.startswith(("=", "+", "-", "@")):
                raise ValueError("candidate CSV contains an invalid public value")
            values.append(value)
        candidates.append(Candidate(*values))
        if len(candidates) > MAX_CANDIDATE_ROWS:
            raise ValueError("candidate CSV exceeds the row limit")
    if not candidates:
        raise ValueError("candidate CSV must contain at least one row")
    return tuple(candidates)


class NoopExecutor:
    """Deterministic synthetic executor used only to prove the approval contract."""

    def __init__(self, failing_finding_ids: Iterable[str] = ()) -> None:
        self.failing_finding_ids = frozenset(failing_finding_ids)
        self.dispatched: list[str] = []

    def dispatch(self, row: dict[str, str]) -> dict[str, str]:
        finding_id = row["finding_id"]
        self.dispatched.append(finding_id)
        if finding_id in self.failing_finding_ids:
            return {"execution_state": "FAILED", "verification_state": "NOT_ATTEMPTED"}
        return {"execution_state": "NOOP_SUCCEEDED", "verification_state": "SYNTHETIC_ONLY"}


class CsvCandidatePilot:
    """Server-side M3A preview/freeze/decision state using native approval semantics."""

    def __init__(self, store: ScaledFindingStore | None = None) -> None:
        self.store = store or ScaledFindingStore()
        self._batches: dict[str, dict[str, Any]] = {}
        self._preparation_revision = 0

    def preview(self, content: bytes) -> dict[str, Any]:
        candidates = parse_candidate_csv(content)
        evidence = self.store.evidence_receipt()
        seen: set[tuple[str, str, str]] = set()
        rows: list[dict[str, str]] = []
        for candidate in candidates:
            base = candidate.public()
            if candidate.key() in seen:
                rows.append({**base, "preview_state": "DUPLICATE", "reason": "DUPLICATE_CANDIDATE"})
                continue
            seen.add(candidate.key())
            resolved = self.store.resolve_candidate(*candidate.key())
            if resolved is None:
                rows.append({**base, "preview_state": "UNKNOWN", "reason": "NOT_IN_CURRENT_EVIDENCE"})
            elif candidate.control_key != PILOT_CONTROL:
                rows.append({**base, "preview_state": "UNSUPPORTED", "reason": "CONTROL_NOT_IN_M3A"})
            elif resolved["config_status"] != "NON_COMPLIANT":
                rows.append({**base, "preview_state": "STALE", "reason": "CURRENT_EVIDENCE_NOT_NON_COMPLIANT"})
            elif resolved["exception_status"] != "NONE":
                rows.append({**base, "preview_state": "EXCLUDED", "reason": "CURRENT_ONE_TIME_EXCEPTION"})
            else:
                rows.append({
                    **base, "finding_id": resolved["finding_id"],
                    "preview_state": "ELIGIBLE", "reason": "CURRENT_EVIDENCE_MATCH",
                })
        rows.sort(key=lambda row: (row["account_alias"], row["control_key"], row["resource_id"], row["preview_state"]))
        eligible = [row for row in rows if row["preview_state"] == "ELIGIBLE"]
        excluded = [row for row in rows if row["preview_state"] == "EXCLUDED"]
        rejected = [row for row in rows if row["preview_state"] not in {"ELIGIBLE", "EXCLUDED"}]
        counts = Counter(row["preview_state"] for row in rows)
        candidate_digest = _digest([candidate.public() for candidate in sorted(candidates, key=Candidate.key)])
        scope = {
            "control": PILOT_CONTROL,
            "eligible": [
                {key: row[key] for key in ("finding_id", "account_alias", "resource_id")}
                for row in eligible
            ],
            "exclusions": [
                {key: row[key] for key in CANDIDATE_FIELDS}
                for row in excluded
            ],
            "candidate_digest": candidate_digest,
            "evidence_version": evidence["version"],
            "evidence_digest": evidence["evidence_digest"],
            "selected_accounts": sorted({row["account_alias"] for row in eligible}),
        }
        return self._freeze_preview(rows, scope)

    def _freeze_preview(self, rows: list[dict[str, str]], scope: dict[str, Any]) -> dict[str, Any]:
        """Shared M3 freeze implementation used by CSV and manual selection pilots."""
        scope_hash = _digest(scope)
        self._preparation_revision += 1
        batch_id = _digest({
            "kind": "synthetic-bulk-m3",
            "scope_hash": scope_hash,
            "preparation_revision": self._preparation_revision,
        })
        batch = {
            "batch_id": batch_id,
            "scope_hash": scope_hash,
            "scope": scope,
            "rows": rows,
            "decision": "PENDING",
            "execution": [],
        }
        view = self._preview_view(batch)
        if not scope["eligible"]:
            view.update({
                "batch_id": None,
                "scope_hash": None,
                "freeze_state": "NO_ELIGIBLE_CANDIDATES",
            })
            return view
        self._batches[batch_id] = batch
        view["freeze_state"] = "FROZEN"
        return view

    def _batch(self, batch_id: str, scope_hash: str) -> dict[str, Any]:
        if not isinstance(batch_id, str) or not isinstance(scope_hash, str):
            raise ValueError("unknown frozen batch")
        batch = self._batches.get(batch_id)
        if batch is None:
            raise ValueError("unknown frozen batch")
        if batch["scope_hash"] != scope_hash:
            raise ValueError("frozen batch scope does not match")
        return batch

    def decide(self, batch_id: str, scope_hash: str, decision: str) -> dict[str, Any]:
        """Native approval adapter: exact batch + scope only, never a wildcard approval."""
        batch = self._batch(batch_id, scope_hash)
        if batch["decision"] != "PENDING":
            raise ValueError("terminal batch cannot be replayed")
        if self.store.evidence_receipt()["evidence_digest"] != batch["scope"]["evidence_digest"]:
            raise ValueError("current evidence changed; re-prepare the candidate scope")
        if decision == "REJECT":
            batch["decision"] = "REJECTED"
        elif decision == "APPROVE":
            batch["decision"] = "APPROVED"
        else:
            raise ValueError("native decision must be APPROVE or REJECT")
        return self.compact_result(batch_id, scope_hash)

    def execute_approved(
        self, batch_id: str, scope_hash: str, executor: NoopExecutor | None = None
    ) -> dict[str, Any]:
        """Invoke a supplied synthetic executor once for the exact approved scope only."""
        batch = self._batch(batch_id, scope_hash)
        if batch["execution"] or batch["decision"] in {"COMPLETED", "PARTIAL", "REJECTED"}:
            raise ValueError("terminal batch cannot be replayed")
        if batch["decision"] != "APPROVED":
            raise ValueError("only an exact native approval can dispatch this batch")
        if self.store.evidence_receipt()["evidence_digest"] != batch["scope"]["evidence_digest"]:
            raise ValueError("current evidence changed; re-prepare the candidate scope")
        executor = executor or NoopExecutor()
        results = []
        for row in batch["rows"]:
            if row["preview_state"] != "ELIGIBLE":
                continue
            outcome = executor.dispatch(row)
            results.append({
                **{key: row[key] for key in ("account_alias", "control_key", "resource_id", "finding_id", "preview_state")},
                **outcome,
            })
        batch["execution"] = results
        batch["decision"] = "COMPLETED" if all(row["execution_state"] == "NOOP_SUCCEEDED" for row in results) else "PARTIAL"
        return self.compact_result(batch_id, scope_hash)

    def _preview_view(self, batch: dict[str, Any]) -> dict[str, Any]:
        counts = Counter(row["preview_state"] for row in batch["rows"])
        rejected = [row for row in batch["rows"] if row["preview_state"] not in {"ELIGIBLE", "EXCLUDED"}]
        return {
            "version": 1,
            "batch_id": batch["batch_id"],
            "scope_hash": batch["scope_hash"],
            "control": PILOT_CONTROL,
            "submitted": len(batch["rows"]),
            "normalized": len(batch["rows"]) - counts["DUPLICATE"],
            "duplicates": counts["DUPLICATE"],
            "eligible": counts["ELIGIBLE"],
            "rejected": len(rejected),
            "excluded": counts["EXCLUDED"],
            "account_count": len(batch["scope"]["selected_accounts"]),
            "candidate_digest": batch["scope"].get("candidate_digest"),
            "selection_digest": batch["scope"].get("selection_digest"),
            "evidence_version": batch["scope"]["evidence_version"],
            "evidence_digest": batch["scope"]["evidence_digest"],
            "rejected_page": rejected[:MAX_REJECTED_PAGE_SIZE],
            "rejected_total": len(rejected),
            "model_context": "COMPACT_SUMMARY_AND_BOUNDED_REJECTIONS",
            "read_only": True,
            "zero_writes": True,
        }

    def compact_result(self, batch_id: str, scope_hash: str) -> dict[str, Any]:
        batch = self._batch(batch_id, scope_hash)
        preview = self._preview_view(batch)
        execution_counts = Counter(row["execution_state"] for row in batch["execution"])
        return {
            **preview,
            "decision": batch["decision"],
            "approved": 1 if batch["decision"] in {"APPROVED", "COMPLETED", "PARTIAL"} else 0,
            "rejected_by_human": 1 if batch["decision"] == "REJECTED" else 0,
            "attempted": len(batch["execution"]),
            "succeeded": execution_counts["NOOP_SUCCEEDED"],
            "failed": execution_counts["FAILED"],
            "executor": "SYNTHETIC_NOOP" if batch["execution"] else "NOT_DISPATCHED",
            "aws_mutation": False,
        }

    def result_csv(self, batch_id: str, scope_hash: str) -> str:
        """Backend-generated full per-row result export; never a model payload."""
        batch = self._batch(batch_id, scope_hash)
        outcomes = {row["finding_id"]: row for row in batch["execution"]}
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=RESULT_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in batch["rows"]:
            outcome = outcomes.get(row.get("finding_id", ""), {})
            writer.writerow({
                "account_alias": _csv_safe(row["account_alias"]),
                "control_key": _csv_safe(row["control_key"]),
                "resource_id": _csv_safe(row["resource_id"]),
                "finding_id": _csv_safe(row.get("finding_id", "")),
                "preview_state": row["preview_state"],
                "execution_state": outcome.get("execution_state", "NOT_DISPATCHED"),
                "verification_state": outcome.get("verification_state", "NOT_ATTEMPTED"),
            })
        return output.getvalue()

    def result_export_receipt(self, batch_id: str, scope_hash: str) -> dict[str, Any]:
        content = self.result_csv(batch_id, scope_hash)
        return {
            "version": 1,
            "filename": RESULT_FILENAME,
            "row_count": max(0, content.count("\n") - 1),
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "content_in_model_context": False,
            "read_only": True,
        }
