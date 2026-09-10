"""Deterministic management backlog over the common finding contract."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable

from .findings import MAX_FINDINGS, REQUIRED_FIELDS, SAFE_TEXT, validate_finding
from .routing import enrich_finding


PRIORITY = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
PLAN_FIELDS = {"owner", "mitigation_plan", "target", "planning_status"}
TRACK_FIELDS = {"finding_id", "first_seen", "last_seen", "occurrence_count", "seen_in_latest_sync", "evidence_origin", "synced_at"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _identity(finding: dict) -> str:
    return hashlib.sha256(json.dumps(_key(finding), separators=(",", ":")).encode()).hexdigest()


def _plan(value: dict) -> dict:
    if not isinstance(value, dict) or set(value) != PLAN_FIELDS:
        raise ValueError("plan requires only owner, mitigation_plan, target, planning_status")
    for field, item in value.items():
        if not isinstance(item, str) or len(item) > (1000 if field == "mitigation_plan" else 128) or (item and not SAFE_TEXT.fullmatch(item)):
            raise ValueError("plan fields must be bounded single-line text")
    if value["planning_status"] not in {"UNPLANNED", "PLANNED"}:
        raise ValueError("planning_status must be UNPLANNED or PLANNED")
    return dict(value)


def _key(finding: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        finding["source"],
        finding["resource_type"],
        finding["resource_id"],
        finding["control"],
    )


class FindingBacklog:
    def __init__(self, findings: Iterable[dict[str, Any]] = (), *, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else None
        self._findings: dict[tuple[str, str, str, str], dict[str, str]] = {}
        if self.path is not None:
            self._load()
        self.upsert(findings)

    def _load(self) -> None:
        try:
            with self.path.open("rb") as stream:
                raw = stream.read(1_000_001)
        except FileNotFoundError:
            return
        except OSError as exc:
            raise RuntimeError("Backlog store is unreadable; startup stopped.") from exc
        try:
            if len(raw) > 1_000_000:
                raise ValueError("store too large")
            payload = json.loads(raw)
            if set(payload) != {"version", "findings"} or payload["version"] != 1 or not isinstance(payload["findings"], list) or len(payload["findings"]) > MAX_FINDINGS:
                raise ValueError("unsupported store")
            loaded = {}
            for item in payload["findings"]:
                if set(item) != set(REQUIRED_FIELDS) | PLAN_FIELDS | TRACK_FIELDS:
                    raise ValueError("invalid stored fields")
                base = validate_finding({key: item[key] for key in REQUIRED_FIELDS})
                _plan({key: item[key] for key in PLAN_FIELDS})
                if item["finding_id"] != _identity(base) or _key(base) in loaded:
                    raise ValueError("invalid or duplicate identity")
                if type(item["occurrence_count"]) is not int or item["occurrence_count"] < 1 or type(item["seen_in_latest_sync"]) is not bool or item["evidence_origin"] not in {"IMPORTED", "AWS_PROVIDER"}:
                    raise ValueError("invalid tracking")
                for field in ("first_seen", "last_seen", "synced_at"):
                    if field == "synced_at" and item[field] == "":
                        continue
                    if datetime.fromisoformat(item[field]).tzinfo is None:
                        raise ValueError("tracking time needs timezone")
                loaded[_key(base)] = item
            self._findings = loaded
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            raise RuntimeError("Backlog store is corrupt or unsupported; startup stopped without overwriting it.") from exc

    def _commit(self, replacement: dict) -> None:
        if len(replacement) > MAX_FINDINGS:
            raise ValueError(f"backlog cannot exceed {MAX_FINDINGS} findings")
        if self.path is not None:
            temporary = None
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                data = json.dumps({"version": 1, "findings": list(replacement.values())}).encode()
                if len(data) > 1_000_000:
                    raise ValueError("backlog exceeds local storage limit")
                with tempfile.NamedTemporaryFile(dir=self.path.parent, prefix=".backlog-", delete=False) as stream:
                    temporary = stream.name
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, self.path)
            except OSError as exc:
                raise RuntimeError("Backlog save failed; previous state retained.") from exc
            finally:
                if temporary and os.path.exists(temporary):
                    os.unlink(temporary)
        self._findings = replacement

    def update_plan(self, finding_id: str, values: dict) -> None:
        plan = _plan(values)
        key = next((key for key, item in self._findings.items() if item["finding_id"] == finding_id), None)
        if key is None:
            raise ValueError("unknown server-owned finding ID")
        self._commit({**self._findings, key: {**self._findings[key], **plan}})

    def _merge(self, replacement: dict, raw: dict, origin: str, now: str, synced_at: str = "") -> tuple:
        finding = validate_finding(raw)
        key = _key(finding)
        old = replacement.get(key, {})
        # Planning belongs to the operator, never subsequent imports or AI output.
        defaults = dict(owner="", target="", mitigation_plan="", planning_status="UNPLANNED")
        finding.update({field: old.get(field, default) for field, default in defaults.items()})
        finding.update(finding_id=_identity(finding), first_seen=old.get("first_seen", now),
                       last_seen=now, occurrence_count=old.get("occurrence_count", 0) + 1,
                       seen_in_latest_sync=True, evidence_origin=origin, synced_at=synced_at)
        replacement[key] = finding
        return key

    def upsert(
        self, findings: Iterable[dict[str, Any]], *, evidence_origin: str = "IMPORTED"
    ) -> None:
        if evidence_origin not in {"IMPORTED", "AWS_PROVIDER"}:
            raise ValueError("evidence origin is unsupported")
        replacement = dict(self._findings)
        now, seen = _now(), set()
        for raw in findings:
            key = _key(validate_finding(raw))
            if key not in seen:
                self._merge(replacement, raw, evidence_origin, now)
                seen.add(key)
        if seen:
            self._commit(replacement)

    def open_findings(self) -> list[dict[str, str]]:
        open_findings = [
            enrich_finding(finding)
            for finding in self._findings.values()
            if finding["status"] == "NON_COMPLIANT"
        ]
        open_findings.sort(
            key=lambda item: (
                PRIORITY[item["severity"]],
                item["observed_at"],
                item["resource_name"],
                item["control"],
            )
        )
        return open_findings

    def replace_provider(self, source: str, findings: list[dict[str, Any]], synced_at: str) -> None:
        replacement = {key: {**value, "seen_in_latest_sync": False} if value["source"] == source and value["evidence_origin"] == "AWS_PROVIDER" else value for key, value in self._findings.items()}
        now, seen = _now(), set()
        for raw in findings:
            finding = validate_finding(raw)
            if finding["source"] != source:
                raise ValueError("provider source mismatch")
            if _key(finding) not in seen:
                seen.add(self._merge(replacement, finding, "AWS_PROVIDER", now, synced_at))
        self._commit(replacement)

    def summary(self) -> dict[str, Any]:
        open_findings = self.open_findings()

        def grouped(field: str) -> list[dict[str, Any]]:
            return [
                {"name": name, "count": count}
                for name, count in sorted(Counter(item[field] for item in open_findings).items())
            ]

        if open_findings:
            first = open_findings[0]
            focus = (
                f"{first['severity']}: {first['control']} on {first['resource_name']}. "
                f"{first['recommendation']}"
            )
        else:
            focus = "No open findings in the bounded provider set."
        return {
            "total_findings": len(self._findings),
            "total_open": len(open_findings),
            "planned": sum(item["planning_status"] == "PLANNED" for item in open_findings),
            "unplanned": sum(item["planning_status"] == "UNPLANNED" for item in open_findings),
            "high_critical": sum(
                item["severity"] in {"HIGH", "CRITICAL"} for item in open_findings
            ),
            "by_source": grouped("source"),
            "by_resource_type": grouped("resource_type"),
            "by_specialist": grouped("specialist_route"),
            "by_eligibility": grouped("action_eligibility"),
            "priority_findings": open_findings[:10],
            "open_findings": open_findings,
            "recommended_focus": focus,
        }
