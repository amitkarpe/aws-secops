"""Common bounded finding contract for Pilot v1.1."""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


MAX_FINDINGS = 100
REQUIRED_FIELDS = (
    "source",
    "resource_type",
    "resource_id",
    "resource_name",
    "environment",
    "control",
    "severity",
    "status",
    "evidence",
    "recommendation",
    "observed_at",
)
SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
STATUSES = {"COMPLIANT", "NON_COMPLIANT"}
OPTIONAL_FIELDS = ("owner", "target")
SAFE_TEXT = re.compile(r"^[^\r\n\x00-\x08\x0b\x0c\x0e-\x1f]+$")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: Any, field: str, *, maximum: int = 500) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"finding field {field} must be a non-empty string")
    value = value.strip()
    if len(value) > maximum or not SAFE_TEXT.fullmatch(value):
        raise ValueError(f"finding field {field} is not bounded plain text")
    return value


def validate_finding(value: dict[str, Any]) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError("each finding must be an object")
    unknown = set(value) - set(REQUIRED_FIELDS) - set(OPTIONAL_FIELDS)
    if unknown:
        raise ValueError(f"unknown finding fields: {', '.join(sorted(unknown))}")
    finding = {
        field: _text(value.get(field), field, maximum=128 if field != "evidence" else 500)
        for field in REQUIRED_FIELDS
    }
    finding.update(
        {
            field: _text(value[field], field, maximum=128)
            for field in OPTIONAL_FIELDS
            if value.get(field)
        }
    )
    finding["severity"] = finding["severity"].upper()
    finding["status"] = finding["status"].upper()
    if finding["severity"] not in SEVERITIES:
        raise ValueError("finding severity is unsupported")
    if finding["status"] not in STATUSES:
        raise ValueError("finding status is unsupported")
    if finding["environment"] not in {"dev", "test", "demo"}:
        raise ValueError("finding environment must be dev, test, or demo")
    try:
        datetime.fromisoformat(finding["observed_at"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("finding observed_at must be ISO-8601") from exc
    return finding


def normalize_sg(provider: dict[str, Any], *, observed_at: str | None = None) -> dict[str, str]:
    status = provider.get("status")
    return validate_finding(
        {
            "source": "AWS EC2",
            "resource_type": "SECURITY_GROUP",
            "resource_id": provider.get("resource_id"),
            "resource_name": provider.get("resource_name"),
            "environment": "dev",
            "control": provider.get("control"),
            "severity": "HIGH" if status == "NON_COMPLIANT" else "INFO",
            "status": status,
            "evidence": f"Provider source: {provider.get('source', 'unknown')}",
            "recommendation": provider.get("recommendation"),
            "observed_at": observed_at or _now(),
        }
    )


S3_SEVERITY = {
    "Block Public Access": "CRITICAL",
    "Default encryption": "HIGH",
    "Versioning": "MEDIUM",
    "TLS-only bucket policy": "HIGH",
    "Object ownership": "MEDIUM",
}


def normalize_s3(provider: dict[str, Any], *, observed_at: str | None = None) -> list[dict[str, str]]:
    timestamp = observed_at or _now()
    findings = []
    for control in provider.get("controls", []):
        status = "COMPLIANT" if control.get("status") == "PASS" else "NON_COMPLIANT"
        findings.append(
            validate_finding(
                {
                    "source": "AWS S3",
                    "resource_type": "S3_BUCKET",
                    "resource_id": provider.get("resource_id"),
                    "resource_name": provider.get("resource_name"),
                    "environment": "dev",
                    "control": control.get("name"),
                    "severity": S3_SEVERITY.get(control.get("name"), "MEDIUM") if status == "NON_COMPLIANT" else "INFO",
                    "status": status,
                    "evidence": control.get("evidence"),
                    "recommendation": (
                        provider.get("recommendation")
                        if status == "NON_COMPLIANT"
                        else "No action required."
                    ),
                    "observed_at": timestamp,
                }
            )
        )
    if len(findings) != 5:
        raise ValueError("S3 provider result must contain exactly five controls")
    return findings


def _bounded(values: Iterable[dict[str, Any]], limit: int) -> list[dict[str, str]]:
    if limit < 1 or limit > MAX_FINDINGS:
        raise ValueError(f"finding import limit must be between 1 and {MAX_FINDINGS}")
    raw = list(values)
    if not raw or len(raw) > limit:
        raise ValueError(f"finding import must contain 1 to {limit} records")
    return [validate_finding(value) for value in raw]


def import_findings(path: str | Path, *, limit: int = MAX_FINDINGS) -> list[dict[str, str]]:
    source = Path(path)
    if source.stat().st_size > 256_000:
        raise ValueError("finding import exceeds 256 KB")
    if source.suffix.lower() == ".json":
        payload = json.loads(source.read_text(encoding="utf-8"))
        values = payload.get("findings") if isinstance(payload, dict) else payload
        if not isinstance(values, list):
            raise ValueError("JSON finding import must contain a list")
        return _bounded(values, limit)
    if source.suffix.lower() == ".csv":
        with source.open(encoding="utf-8", newline="") as handle:
            return _bounded(csv.DictReader(handle), limit)
    raise ValueError("finding import must be .json or .csv")
