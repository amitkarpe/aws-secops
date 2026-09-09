"""Two explicit public-safe source adapters for Platform Phase 1."""

from __future__ import annotations

from typing import Any, Callable

from .findings import decode_records, validate_finding


CLOUDSCAPE_FIELDS = {
    "asset_type",
    "asset_id",
    "asset_name",
    "environment",
    "control_id",
    "risk",
    "compliance",
    "evidence",
    "recommended_action",
    "observed_at",
}
VAPT_FIELDS = {
    "asset_id",
    "asset_name",
    "environment",
    "vulnerability_id",
    "severity",
    "status",
    "evidence",
    "recommended_action",
    "observed_at",
}


def _exact_fields(record: dict[str, Any], expected: set[str], source: str) -> None:
    missing = expected - set(record)
    unknown = set(record) - expected
    if missing or unknown:
        detail = []
        if missing:
            detail.append(f"missing {', '.join(sorted(missing))}")
        if unknown:
            detail.append(f"unknown {', '.join(sorted(str(field) for field in unknown))}")
        raise ValueError(f"{source} record fields are invalid: {'; '.join(detail)}")


def _cloudscape(record: dict[str, Any]) -> dict[str, str]:
    _exact_fields(record, CLOUDSCAPE_FIELDS, "CloudSCAPE")
    status = {"PASS": "COMPLIANT", "FAIL": "NON_COMPLIANT"}.get(
        str(record["compliance"]).upper()
    )
    if status is None:
        raise ValueError("CloudSCAPE compliance must be PASS or FAIL")
    if record["asset_type"] not in {"SECURITY_GROUP", "S3_BUCKET", "EC2_INSTANCE"}:
        raise ValueError("CloudSCAPE asset_type is unsupported")
    return validate_finding(
        {
            "source": "CloudSCAPE",
            "resource_type": record["asset_type"],
            "resource_id": record["asset_id"],
            "resource_name": record["asset_name"],
            "environment": record["environment"],
            "control": record["control_id"],
            "severity": record["risk"],
            "status": status,
            "evidence": record["evidence"],
            "recommendation": record["recommended_action"],
            "observed_at": record["observed_at"],
        }
    )


def _vapt(record: dict[str, Any]) -> dict[str, str]:
    _exact_fields(record, VAPT_FIELDS, "VAPT")
    status = {"OPEN": "NON_COMPLIANT", "CLOSED": "COMPLIANT"}.get(
        str(record["status"]).upper()
    )
    if status is None:
        raise ValueError("VAPT status must be OPEN or CLOSED")
    return validate_finding(
        {
            "source": "VAPT",
            "resource_type": "EC2_INSTANCE",
            "resource_id": record["asset_id"],
            "resource_name": record["asset_name"],
            "environment": record["environment"],
            "control": record["vulnerability_id"],
            "severity": record["severity"],
            "status": status,
            "evidence": record["evidence"],
            "recommendation": record["recommended_action"],
            "observed_at": record["observed_at"],
        }
    )


ADAPTERS: dict[str, Callable[[dict[str, Any]], dict[str, str]]] = {
    "cloudscape": _cloudscape,
    "vapt": _vapt,
}


def adapt_source(content: bytes, filename: str, source_format: str) -> list[dict[str, str]]:
    try:
        adapter = ADAPTERS[source_format]
    except KeyError as exc:
        raise ValueError("source format must be cloudscape or vapt") from exc
    return [adapter(record) for record in decode_records(content, filename)]
