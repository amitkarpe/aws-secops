"""Bounded read-only evidence boundary for the persistent AWS MCP path.

The adapter accepts only fixed SecOps query families.  It deliberately does not
accept service names, AWS operations, scripts, resource identifiers, or request
parameters from a model.  A transport implementation is responsible for the
hosted MCP call and returns one already-decoded page at a time.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import os
import re
from typing import Any, Mapping, Protocol, Sequence


class EvidenceQuery(str, Enum):
    CONFIG_COMPLIANCE = "config-compliance-summary"
    S3_POSTURE = "s3-public-access-posture"
    SECURITY_GROUP_EXPOSURE = "security-group-exposure"
    INSPECTOR_SUMMARY = "inspector-summary"


MAX_RESULTS = 100
MAX_PAGES = 3
MAX_TEXT = 160
_ACCOUNT_ID = re.compile(r"^[0-9]{12}$")
_RESOURCE_REF = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:/-]{0,127}$")
_STATUSES = {
    "COMPLIANT",
    "NON_COMPLIANT",
    "INSUFFICIENT_DATA",
    "NOT_APPLICABLE",
    "NOT_REPORTED",
}
_INSPECTOR_STATUSES = {"ENABLED", "DISABLED", "SUSPENDED"}
_FINDING_SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL")
_SENSITIVE_KEY_MARKERS = ("accesskey", "authorization", "credential", "password", "secret", "token")


class EvidenceProviderError(RuntimeError):
    """Safe error with a stable public reason code."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class AccountScope:
    alias: str
    expected_account_id: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"lab-[a-z0-9-]{1,28}", self.alias):
            raise ValueError("account alias is outside the LAB contract")
        if not _ACCOUNT_ID.fullmatch(self.expected_account_id):
            raise ValueError("expected account identity is invalid")


@dataclass(frozen=True)
class TransportPage:
    verified_account_id: str
    collected_at: str
    items: Sequence[Mapping[str, Any]]
    next_token: str | None = None
    partial: bool = False


class ReadOnlyEvidenceTransport(Protocol):
    """Server-side transport; never expose this protocol as a model tool."""

    def read_page(
        self,
        query: EvidenceQuery,
        *,
        next_token: str | None,
        limit: int,
    ) -> TransportPage: ...


def persistent_mcp_enabled(environ: Mapping[str, str] | None = None) -> bool:
    """The integration gate is fail-closed and disabled by default."""

    values = os.environ if environ is None else environ
    return values.get("SECOPS_PERSISTENT_MCP_EVIDENCE_ENABLED", "0") == "1"


def _public_ref(account_id: str) -> str:
    return "acct-" + hashlib.sha256(account_id.encode("ascii")).hexdigest()[:12]


def _timestamp(value: str) -> datetime:
    if not isinstance(value, str) or len(value) > 40:
        raise EvidenceProviderError("INVALID_TIMESTAMP")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceProviderError("INVALID_TIMESTAMP") from exc
    if parsed.tzinfo is None:
        raise EvidenceProviderError("INVALID_TIMESTAMP")
    return parsed


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
            if any(marker in normalized for marker in _SENSITIVE_KEY_MARKERS) or _contains_sensitive_key(child):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_sensitive_key(child) for child in value)
    return False


def _resource_ref(value: Any) -> str:
    if not isinstance(value, str) or not _RESOURCE_REF.fullmatch(value):
        raise EvidenceProviderError("INVALID_RESOURCE_REFERENCE")
    return value


def _nonnegative_int(value: Any) -> int:
    if type(value) is not int or value < 0:
        raise EvidenceProviderError("INVALID_COUNT")
    return value


def _normalize_config(item: Mapping[str, Any]) -> dict[str, Any]:
    if set(item) != {"control", "status", "affected_resources"}:
        raise EvidenceProviderError("INVALID_CONFIG_EVIDENCE")
    control = item["control"]
    status = item["status"]
    if not isinstance(control, str) or not 1 <= len(control) <= MAX_TEXT or status not in _STATUSES:
        raise EvidenceProviderError("INVALID_CONFIG_EVIDENCE")
    return {
        "affected_resources": _nonnegative_int(item["affected_resources"]),
        "control": control,
        "status": status,
    }


def _normalize_s3(item: Mapping[str, Any]) -> dict[str, Any]:
    if set(item) != {"resource_ref", "all_public_access_blocked"}:
        raise EvidenceProviderError("INVALID_S3_EVIDENCE")
    blocked = item["all_public_access_blocked"]
    if type(blocked) is not bool:
        raise EvidenceProviderError("INVALID_S3_EVIDENCE")
    return {"all_public_access_blocked": blocked, "resource_ref": _resource_ref(item["resource_ref"])}


def _normalize_security_group(item: Mapping[str, Any]) -> dict[str, Any]:
    if set(item) != {"resource_ref", "unrestricted_ssh"}:
        raise EvidenceProviderError("INVALID_SECURITY_GROUP_EVIDENCE")
    exposed = item["unrestricted_ssh"]
    if type(exposed) is not bool:
        raise EvidenceProviderError("INVALID_SECURITY_GROUP_EVIDENCE")
    return {"resource_ref": _resource_ref(item["resource_ref"]), "unrestricted_ssh": exposed}


def _normalize_inspector(item: Mapping[str, Any]) -> dict[str, Any]:
    if set(item) != {"status", "finding_counts"} or item["status"] not in _INSPECTOR_STATUSES:
        raise EvidenceProviderError("INVALID_INSPECTOR_EVIDENCE")
    counts = item["finding_counts"]
    if not isinstance(counts, Mapping) or set(counts) - set(_FINDING_SEVERITIES):
        raise EvidenceProviderError("INVALID_INSPECTOR_EVIDENCE")
    normalized = {severity: _nonnegative_int(counts.get(severity, 0)) for severity in _FINDING_SEVERITIES}
    return {"finding_counts": normalized, "status": item["status"]}


_NORMALIZERS = {
    EvidenceQuery.CONFIG_COMPLIANCE: _normalize_config,
    EvidenceQuery.S3_POSTURE: _normalize_s3,
    EvidenceQuery.SECURITY_GROUP_EXPOSURE: _normalize_security_group,
    EvidenceQuery.INSPECTOR_SUMMARY: _normalize_inspector,
}


class PersistentMcpEvidenceProvider:
    """Normalize fixed persistent-MCP reads into a public-safe envelope."""

    def __init__(self, transport: ReadOnlyEvidenceTransport, scope: AccountScope):
        self._transport = transport
        self._scope = scope

    def collect(self, query: EvidenceQuery) -> dict[str, Any]:
        if not isinstance(query, EvidenceQuery):
            raise ValueError("unsupported evidence query")

        items: list[dict[str, Any]] = []
        next_token: str | None = None
        seen_tokens: set[str] = set()
        partial = False
        collected_at: str | None = None
        collected_instant: datetime | None = None
        try:
            for _ in range(MAX_PAGES):
                requested_limit = min(50, MAX_RESULTS - len(items))
                page = self._transport.read_page(
                    query,
                    next_token=next_token,
                    limit=requested_limit,
                )
                if not isinstance(page, TransportPage):
                    raise EvidenceProviderError("INVALID_TRANSPORT_PAGE")
                if page.verified_account_id != self._scope.expected_account_id:
                    raise EvidenceProviderError("ACCOUNT_MISMATCH")
                if _contains_sensitive_key(page.items):
                    raise EvidenceProviderError("SENSITIVE_MATERIAL_REJECTED")
                page_instant = _timestamp(page.collected_at)
                if collected_instant is None or page_instant > collected_instant:
                    collected_at = page.collected_at
                    collected_instant = page_instant
                if not isinstance(page.items, (list, tuple)) or len(page.items) > requested_limit:
                    raise EvidenceProviderError("PAGE_LIMIT_EXCEEDED")
                normalizer = _NORMALIZERS[query]
                for raw in page.items:
                    if not isinstance(raw, Mapping):
                        raise EvidenceProviderError("INVALID_EVIDENCE_ITEM")
                    if len(items) == MAX_RESULTS:
                        partial = True
                        break
                    items.append(normalizer(raw))
                partial = partial or page.partial
                token = page.next_token
                if token is None:
                    next_token = None
                    break
                if not isinstance(token, str) or not token or len(token) > MAX_TEXT or token in seen_tokens:
                    raise EvidenceProviderError("INVALID_PAGINATION_TOKEN")
                seen_tokens.add(token)
                next_token = token
                if len(items) == MAX_RESULTS:
                    partial = True
                    break
            if next_token is not None:
                partial = True
        except EvidenceProviderError as exc:
            return self._unavailable(query, exc.code)
        except Exception:
            return self._unavailable(query, "TRANSPORT_UNAVAILABLE")

        items.sort(key=lambda row: tuple(str(row[key]) for key in sorted(row)))
        return self._envelope(
            query,
            state="PARTIAL" if partial else "AVAILABLE",
            collected_at=collected_at,
            items=items,
            partial=partial,
        )

    def _unavailable(self, query: EvidenceQuery, reason: str) -> dict[str, Any]:
        value = self._envelope(query, state="UNAVAILABLE", collected_at=None, items=[], partial=False)
        value["reason"] = reason
        return value

    def _envelope(
        self,
        query: EvidenceQuery,
        *,
        state: str,
        collected_at: str | None,
        items: list[dict[str, Any]],
        partial: bool,
    ) -> dict[str, Any]:
        return {
            "version": 1,
            "query": query.value,
            "state": state,
            "source": {
                "provider": "persistent-aws-mcp",
                "provenance": "AWS Managed MCP through the persistent read-only runtime",
            },
            "account": {
                "alias": self._scope.alias,
                "identity_verified": state != "UNAVAILABLE",
                "public_ref": _public_ref(self._scope.expected_account_id),
            },
            "collected_at": collected_at,
            "items": items,
            "item_count": len(items),
            "partial": partial,
            "read_only": True,
            "mutation": False,
        }
