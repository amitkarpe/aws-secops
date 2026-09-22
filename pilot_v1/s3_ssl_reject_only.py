"""Exact s3_ssl native-decision contract with no execution capability.

This is intentionally separate from the CodeBuild-capable S3 BPA/SSH route.
It accepts only a current read receipt, freezes one exact public-safe finding,
and records terminal decisions.  Approve is an explicit blocked outcome.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping

CONTROL = "s3_ssl"


def _digest(value: Any, length: int) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:length]


@dataclass
class S3SslRejectOnlyDecision:
    """One-use, exact-scope decision state; it has no dispatch dependency."""
    evidence: Mapping[str, Any]
    events: list[dict[str, Any]] = field(default_factory=list)
    _batch: dict[str, str] | None = None

    def prepare(self, *, alias: str) -> dict[str, str]:
        if self._batch is not None:
            raise ValueError("s3_ssl batch already terminal or pending")
        if self.evidence.get("control") != CONTROL or self.evidence.get("read_only") is not True:
            raise ValueError("exact read-only s3_ssl evidence required")
        account = next((row for row in self.evidence.get("accounts", []) if row.get("alias") == alias), None)
        if not isinstance(account, Mapping) or account.get("identity_verified") is not True or account.get("state") != "AVAILABLE":
            raise ValueError("selected alias has no verified current evidence")
        finding = next((row for row in account.get("statuses", []) if row.get("status") == "NON_COMPLIANT"), None)
        if not isinstance(finding, Mapping) or not isinstance(finding.get("resource_ref"), str):
            raise ValueError("selected alias has no current s3_ssl finding")
        frozen = {"control": CONTROL, "alias": alias, "resource_ref": finding["resource_ref"], "evidence_digest": self.evidence.get("evidence_digest")}
        self._batch = {"batch_id": _digest(frozen, 20), "scope_hash": _digest(frozen, 24)}
        self.events.append({"event": "PREPARE_FROZEN", **self._batch, "control": CONTROL})
        return dict(self._batch)

    def decide(self, *, batch_id: str, scope_hash: str, decision: str) -> dict[str, Any]:
        if self._batch != {"batch_id": batch_id, "scope_hash": scope_hash}:
            raise ValueError("submitted decision does not match frozen s3_ssl scope")
        if decision not in {"reject", "approve"}:
            raise ValueError("native decision must be approve or reject")
        self._batch = None
        if decision == "reject":
            value = {"decision": "REJECTED", "remediation_dispatches": 0, "aws_writes": 0}
        elif decision == "approve":
            value = {"decision": "LIVE_EXECUTION_NOT_AUTHORIZED", "remediation_dispatches": 0, "aws_writes": 0}
        self.events.append({"event": "NATIVE_APPROVAL_DECISION", "control": CONTROL, **value})
        return value
