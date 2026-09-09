"""Common bounded finding contract for Pilot v1.1."""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_FINDINGS = 100
MAX_IMPORT_BYTES = 256_000
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
    if "buckets" in provider:
        buckets = provider.get("buckets", [])
        exceptions = provider.get("exceptions", [])
        if not isinstance(buckets, list) or not 1 <= len(buckets) <= 5:
            raise ValueError("S3 provider aggregate must contain 1 to 5 buckets")
        if not isinstance(exceptions, list):
            raise ValueError("S3 provider aggregate exceptions must be a list")
        bucket_ids = [item.get("resource_id") for item in buckets]
        if len(bucket_ids) != len(set(bucket_ids)) or any(not item for item in bucket_ids):
            raise ValueError("S3 provider aggregate bucket identities must be unique")
        exception_keys = {
            (item.get("resource_id"), item.get("control")) for item in exceptions
        }
        if (
            len(exception_keys) != len(exceptions)
            or any(item.get("resource_id") not in bucket_ids for item in exceptions)
            or provider.get("fail_count") != len(exceptions)
        ):
            raise ValueError("S3 provider aggregate exceptions do not match its buckets")
        findings = []
        for bucket in buckets:
            bucket_exceptions = [
                item
                for item in exceptions
                if item.get("resource_id") == bucket.get("resource_id")
            ]
            if not bucket_exceptions:
                findings.append(
                    validate_finding(
                        {
                            "source": "AWS S3",
                            "resource_type": "S3_BUCKET",
                            "resource_id": bucket.get("resource_id"),
                            "resource_name": bucket.get("resource_name"),
                            "environment": "dev",
                            "control": "five-control S3 baseline",
                            "severity": "INFO",
                            "status": "COMPLIANT",
                            "evidence": "5 of 5 provider controls passed.",
                            "recommendation": "No action required.",
                            "observed_at": timestamp,
                        }
                    )
                )
            for item in bucket_exceptions:
                findings.append(
                    validate_finding(
                        {
                            "source": "AWS S3",
                            "resource_type": "S3_BUCKET",
                            "resource_id": bucket.get("resource_id"),
                            "resource_name": bucket.get("resource_name"),
                            "environment": "dev",
                            "control": item.get("control"),
                            "severity": S3_SEVERITY.get(item.get("control"), "MEDIUM"),
                            "status": "NON_COMPLIANT",
                            "evidence": item.get("evidence"),
                            "recommendation": provider.get("recommendation"),
                            "observed_at": timestamp,
                        }
                    )
                )
        return findings

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


def decode_records(
    content: bytes, filename: str, *, limit: int = MAX_FINDINGS
) -> list[dict[str, Any]]:
    if len(content) > MAX_IMPORT_BYTES:
        raise ValueError("finding import exceeds 256 KB")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("finding import must be UTF-8") from exc
    suffix = Path(filename).suffix.lower()
    if suffix == ".json":
        payload = json.loads(text)
        values = payload.get("findings") if isinstance(payload, dict) else payload
        if not isinstance(values, list):
            raise ValueError("JSON finding import must contain a list")
        raw = values
    elif suffix == ".csv":
        raw = list(csv.DictReader(io.StringIO(text, newline="")))
    else:
        raise ValueError("finding import must be .json or .csv")
    if limit < 1 or limit > MAX_FINDINGS:
        raise ValueError(f"finding import limit must be between 1 and {MAX_FINDINGS}")
    if not raw or len(raw) > limit:
        raise ValueError(f"finding import must contain 1 to {limit} records")
    if not all(isinstance(value, dict) for value in raw):
        raise ValueError("each source record must be an object")
    return raw


def import_findings_content(
    content: bytes, filename: str, *, limit: int = MAX_FINDINGS
) -> list[dict[str, str]]:
    return [validate_finding(value) for value in decode_records(content, filename, limit=limit)]


def import_findings(path: str | Path, *, limit: int = MAX_FINDINGS) -> list[dict[str, str]]:
    source = Path(path)
    return import_findings_content(source.read_bytes(), source.name, limit=limit)
