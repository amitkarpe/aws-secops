"""Deterministic, read-only 1K finding truth and bounded query/export APIs."""
from __future__ import annotations

import csv
import hashlib
import io
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable

CONTROLS = ("s3_ssl", "s3_logging", "s3_backup", "restricted_ssh")
CONFIG_STATUSES = frozenset({"COMPLIANT", "NON_COMPLIANT"})
PROVIDER_STATUSES = frozenset({"UNVERIFIED"})
EXCEPTION_STATUSES = frozenset({"NONE", "ONE_TIME_TEST_EXCEPTION"})
REMEDIATION_STATUSES = frozenset({"NOT_STARTED"})
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 25
SEARCH_FIELDS = ("account_alias", "control_key", "resource_type", "resource_id")
SORT_FIELDS = (
    "finding_id", "account_alias", "region", "control_key", "resource_type",
    "resource_id", "config_status", "provider_status", "exception_status",
    "remediation_status", "last_evaluated",
)
CSV_FIELDS = (
    "account_alias", "region", "control_key", "resource_type", "resource_id",
    "config_status", "provider_status", "exception_status", "remediation_status",
    "last_evaluated",
)
ROW_FIELDS = frozenset(("finding_id",) + CSV_FIELDS)
ALIASES = frozenset(f"lab-{number:03d}" for number in range(1, 51))


def generate_findings() -> tuple[dict[str, str], ...]:
    """Generate the compact public fixture contract without randomness."""
    rows: list[dict[str, str]] = []
    control_parts = {
        "s3_ssl": ("S3_BUCKET", "ssl"),
        "s3_logging": ("S3_BUCKET", "log"),
        "s3_backup": ("S3_BUCKET", "bak"),
        "restricted_ssh": ("SECURITY_GROUP", "ssh"),
    }
    for account_number in range(1, 51):
        alias = f"lab-{account_number:03d}"
        for control in CONTROLS:
            resource_type, short = control_parts[control]
            for resource_number in range(1, 6):
                prefix = "bucket" if resource_type == "S3_BUCKET" else "sg"
                rows.append({
                    "finding_id": f"f-{alias}-{control}-{resource_number:02d}",
                    "account_alias": alias,
                    "region": "ap-southeast-1",
                    "control_key": control,
                    "resource_type": resource_type,
                    "resource_id": f"{prefix}-{alias}-{short}-{resource_number:02d}",
                    "config_status": "NON_COMPLIANT",
                    "provider_status": "UNVERIFIED",
                    "exception_status": (
                        "ONE_TIME_TEST_EXCEPTION" if resource_number == 5 else "NONE"
                    ),
                    "remediation_status": "NOT_STARTED",
                    "last_evaluated": "2026-09-22T00:00:00Z",
                })
    return tuple(rows)


@dataclass(frozen=True)
class FindingQuery:
    control_key: str | None = None
    account_alias: str | None = None
    config_status: str | None = None
    exception_status: str | None = None
    search: str | None = None
    sort_by: str = "finding_id"
    sort_direction: str = "asc"
    page: int = 1
    limit: int = DEFAULT_PAGE_SIZE


def _validate_query(query: FindingQuery) -> None:
    if query.control_key is not None and query.control_key not in CONTROLS:
        raise ValueError("unsupported control_key")
    if query.account_alias is not None and (
        not isinstance(query.account_alias, str)
        or query.account_alias not in ALIASES
    ):
        raise ValueError("unsupported account_alias")
    if query.config_status is not None and query.config_status not in CONFIG_STATUSES:
        raise ValueError("unsupported config_status")
    if query.exception_status is not None and query.exception_status not in EXCEPTION_STATUSES:
        raise ValueError("unsupported exception_status")
    if query.search is not None and (
        not isinstance(query.search, str) or not query.search.strip() or len(query.search) > 128
    ):
        raise ValueError("search must be 1 to 128 characters")
    if query.sort_by not in SORT_FIELDS or query.sort_direction not in {"asc", "desc"}:
        raise ValueError("unsupported sort")
    if type(query.page) is not int or query.page < 1:
        raise ValueError("page must be a positive integer")
    if type(query.limit) is not int or not 1 <= query.limit <= MAX_PAGE_SIZE:
        raise ValueError(f"limit must be between 1 and {MAX_PAGE_SIZE}")


class ScaledFindingStore:
    """Server-owned truth; model-facing methods return only summaries or one page."""

    def __init__(self, rows: Iterable[dict[str, str]] | None = None) -> None:
        self._rows = tuple(dict(row) for row in (rows if rows is not None else generate_findings()))
        if len(self._rows) != 1000:
            raise ValueError("scaled finding truth must contain exactly 1,000 unique findings")
        if any(not _valid_row(row) for row in self._rows):
            raise ValueError("scaled finding truth contains an invalid or private field")
        if len({row["finding_id"] for row in self._rows}) != 1000:
            raise ValueError("scaled finding truth must contain exactly 1,000 unique findings")

    def _filtered(self, query: FindingQuery) -> list[dict[str, str]]:
        _validate_query(query)
        rows = self._rows
        for field in ("control_key", "account_alias", "config_status", "exception_status"):
            value = getattr(query, field)
            if value is not None:
                rows = tuple(row for row in rows if row[field] == value)
        if query.search is not None:
            needle = query.search.strip().casefold()
            rows = tuple(
                row for row in rows
                if any(needle in row[field].casefold() for field in SEARCH_FIELDS)
            )
        return sorted(
            (dict(row) for row in rows),
            key=lambda row: (row[query.sort_by], row["finding_id"]),
            reverse=query.sort_direction == "desc",
        )

    def summary(self) -> dict[str, Any]:
        controls = Counter(row["control_key"] for row in self._rows)
        statuses = Counter(row["config_status"] for row in self._rows)
        exceptions = Counter(row["exception_status"] for row in self._rows)
        return {
            "version": 1,
            "fixture": "synthetic-1k",
            "total_findings": len(self._rows),
            "account_count": len({row["account_alias"] for row in self._rows}),
            "control_counts": {key: controls[key] for key in CONTROLS},
            "config_status_counts": dict(sorted(statuses.items())),
            "exception_status_counts": dict(sorted(exceptions.items())),
            "read_only": True,
        }

    def query(self, query: FindingQuery = FindingQuery()) -> dict[str, Any]:
        rows = self._filtered(query)
        start = (query.page - 1) * query.limit
        page_rows = rows[start:start + query.limit]
        return {
            "version": 1,
            "fixture": "synthetic-1k",
            "total_count": len(rows),
            "returned_count": len(page_rows),
            "page": query.page,
            "limit": query.limit,
            "page_count": (len(rows) + query.limit - 1) // query.limit,
            "items": page_rows,
            "read_only": True,
            "model_context": "ONE_BOUNDED_PAGE",
        }

    def export_csv(self, query: FindingQuery = FindingQuery()) -> str:
        """Return backend export bytes; callers must not place this in model context."""
        rows = self._filtered(query)
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_safe(row[field]) for field in CSV_FIELDS})
        return output.getvalue()

    def export_receipt(self, query: FindingQuery = FindingQuery()) -> dict[str, Any]:
        """Return model-safe export metadata, never the CSV payload."""
        content = self.export_csv(query)
        row_count = max(0, content.count("\n") - 1)
        return {
            "version": 1,
            "filename": "compliance-findings.csv",
            "row_count": row_count,
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "content_in_model_context": False,
            "read_only": True,
        }


def _csv_safe(value: str) -> str:
    return f"'{value}" if value.startswith(("=", "+", "-", "@")) else value


def _valid_row(row: dict[str, str]) -> bool:
    return (
        set(row) == ROW_FIELDS
        and all(isinstance(value, str) for value in row.values())
        and row["account_alias"] in ALIASES
        and row["region"] == "ap-southeast-1"
        and row["control_key"] in CONTROLS
        and row["resource_type"] in {"S3_BUCKET", "SECURITY_GROUP"}
        and row["config_status"] in CONFIG_STATUSES
        and row["provider_status"] in PROVIDER_STATUSES
        and row["exception_status"] in EXCEPTION_STATUSES
        and row["remediation_status"] in REMEDIATION_STATUSES
        and bool(re.fullmatch(r"[a-z0-9_-]{1,128}", row["finding_id"]))
        and bool(re.fullmatch(r"[a-z0-9_-]{1,128}", row["resource_id"]))
        and row["last_evaluated"] == "2026-09-22T00:00:00Z"
    )


def model_read(
    mode: str,
    *,
    control_key: str | None = None,
    account_alias: str | None = None,
    config_status: str | None = None,
    exception_status: str | None = None,
    search: str | None = None,
    sort_by: str = "finding_id",
    sort_direction: str = "asc",
    page: int = 1,
    limit: int = DEFAULT_PAGE_SIZE,
) -> dict[str, Any]:
    """Product-facing read path whose return value is always model-bounded."""
    store = ScaledFindingStore()
    if mode == "summary":
        return store.summary()
    query = FindingQuery(
        control_key=control_key,
        account_alias=account_alias,
        config_status=config_status,
        exception_status=exception_status,
        search=search,
        sort_by=sort_by,
        sort_direction=sort_direction,
        page=page,
        limit=limit,
    )
    if mode == "page":
        return store.query(query)
    if mode == "export":
        return store.export_receipt(query)
    raise ValueError("mode must be summary, page, or export")
