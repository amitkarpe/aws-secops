"""Strict read-only client for the unified four-account Config backend."""
from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

ALIASES = ("lab-dev", "lab-poc", "lab-qa", "lab-sec")
CONTROLS = (
    "s3-bucket-level-public-access-prohibited",
    "restricted-ssh",
)
STATUSES = {"COMPLIANT", "NON_COMPLIANT", "INSUFFICIENT_DATA", "NOT_REPORTED", "NOT_APPLICABLE"}
MAX_BACKEND_BYTES = 512 * 1024
MAX_IDENTIFIER_CHARS = 128
MAX_RESOURCE_IDS = 4


class BackendEvidenceError(RuntimeError):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise BackendEvidenceError("Config backend redirect rejected")


def _base(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise BackendEvidenceError("Config backend must be loopback HTTP")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise BackendEvidenceError("Config backend URL is not canonical")
    port = parsed.port or 80
    if port != 1111:
        raise BackendEvidenceError("Config backend must use loopback port 1111")
    return f"http://{parsed.hostname}:{port}"


def _get_json(base_url: str, path: str, *, timeout: float = 65.0) -> dict[str, Any]:
    base = _base(base_url)
    request = Request(base + path, headers={"Origin": base, "Accept": "application/json"})
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            content_type = response.headers.get("content-type", "")
            if response.status != 200 or "application/json" not in content_type.lower():
                raise BackendEvidenceError("Config backend returned an unexpected response")
            raw = response.read(MAX_BACKEND_BYTES + 1)
            if len(raw) > MAX_BACKEND_BYTES:
                raise BackendEvidenceError("Config backend response is too large")
            try:
                value = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise BackendEvidenceError("Config backend returned invalid JSON") from exc
    except BackendEvidenceError:
        raise
    except Exception as exc:
        raise BackendEvidenceError("Config backend unavailable") from exc
    if not isinstance(value, dict):
        raise BackendEvidenceError("Config backend returned invalid JSON")
    return value


def _optional_identifiers(row: dict[str, Any]) -> dict[str, Any]:
    """Preserve a bounded subset of authorized identifiers supplied by the backend."""
    out: dict[str, Any] = {}

    account_values = {
        row.get(key) for key in ("accountId", "AccountId")
        if isinstance(row.get(key), str) and row.get(key).isdigit() and len(row.get(key)) == 12
    }
    if len(account_values) == 1:
        out["account_id"] = next(iter(account_values))

    resource_values = {
        row.get(key) for key in ("resourceId", "ResourceId")
        if isinstance(row.get(key), str) and 1 <= len(row.get(key)) <= MAX_IDENTIFIER_CHARS
    }
    if len(resource_values) == 1:
        out["resource_id"] = next(iter(resource_values))

    values = row.get("resourceIds")
    if isinstance(values, list) and values:
        limited = values[:MAX_RESOURCE_IDS]
        if all(isinstance(x, str) and 1 <= len(x) <= MAX_IDENTIFIER_CHARS for x in limited):
            out["resource_ids"] = limited
            if len(values) > MAX_RESOURCE_IDS:
                out["resource_ids_truncated"] = True
                out["resource_ids_supplied"] = len(values)
    return out


def current_evidence(base_url: str = "http://127.0.0.1:1111") -> dict[str, Any]:
    diagnostics = _get_json(base_url, "/api/diagnostics")
    provider = diagnostics.get("components", {}).get("configProvider", {})
    if provider.get("status") != "READY":
        raise BackendEvidenceError("Four-account Config provider is not READY")

    snapshot = _get_json(base_url, "/api/controls?environment=ALL&refresh=1")
    if (snapshot.get("environment") != "ALL" or snapshot.get("available") is not True
            or snapshot.get("partial") is not False
            or snapshot.get("availableAccounts") != 4 or snapshot.get("totalAccounts") != 4):
        raise BackendEvidenceError("Four-account Config snapshot is incomplete")

    accounts = snapshot.get("accounts")
    if not isinstance(accounts, list):
        raise BackendEvidenceError("Config account evidence is invalid")
    aliases = [x.get("alias") for x in accounts if isinstance(x, dict) and x.get("available") is True]
    if tuple(sorted(aliases)) != tuple(sorted(ALIASES)) or len(aliases) != 4:
        raise BackendEvidenceError("Config aliases do not match the registered LAB scope")

    rules = snapshot.get("rules")
    if not isinstance(rules, list) or len(rules) != 8:
        raise BackendEvidenceError("Expected exactly eight account/control checks")

    checks: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in rules:
        if not isinstance(row, dict):
            raise BackendEvidenceError("Config rule evidence is invalid")
        alias = row.get("accountAlias")
        control = row.get("ConfigRuleName")
        status = row.get("status")
        count = row.get("count")
        key = (alias, control)
        if alias not in ALIASES or control not in CONTROLS or status not in STATUSES or key in seen:
            raise BackendEvidenceError("Config rule evidence is outside the v1 contract")
        if not isinstance(count, int) or count < 0:
            raise BackendEvidenceError("Config affected count is invalid")
        seen.add(key)
        item = {
            "account_alias": alias,
            "control": control,
            "status": status,
            "affected_resources": count,
        }
        item.update(_optional_identifiers(row))
        checks.append(item)

    expected = {(a, c) for a in ALIASES for c in CONTROLS}
    if seen != expected:
        raise BackendEvidenceError("Config evidence does not contain the exact v1 matrix")

    checks.sort(key=lambda x: (ALIASES.index(x["account_alias"]), CONTROLS.index(x["control"])))
    identifier_keys = {"account_id", "resource_id", "resource_ids"}
    identifiers_available = any(identifier_keys.intersection(item) for item in checks)
    return {
        "version": 1,
        "source": "Unified Config backend",
        "fetched_at": snapshot.get("fetchedAt"),
        "aliases": list(ALIASES),
        "controls": list(CONTROLS),
        "checks": checks,
        "identifiers_available": identifiers_available,
        "diagnostics": {
            "config_provider": "READY",
            "overall": diagnostics.get("status"),
        },
        "read_only": True,
    }
