"""Public-safe capability metadata for the Compliance Agent.

This module consumes only a sanitized contract.  It has no finding reader,
executor, AWS client, or approval side effect.  Capability metadata can route a
request toward an existing product path, but it can never authorize execution.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
import re
from typing import Any, Mapping


CAPABILITY_STATES = ("DETECT", "EXPLAIN", "PREPARE", "REMEDIATE", "VERIFY")
APPROVED_CONTROLS = {
    "s3_ssl": "AWS::S3::Bucket",
    "s3_logging": "AWS::S3::Bucket",
    "s3_backup": "AWS::S3::Bucket",
    "restricted_ssh": "AWS::EC2::SecurityGroup",
}
_SUPPORT_FIELDS = {
    "DETECT": "supports_detect",
    "EXPLAIN": "supports_explain",
    "PREPARE": "supports_prepare",
    "REMEDIATE": "supports_remediate",
    "VERIFY": "supports_verify",
}
_RECORD_FIELDS = {
    "control_key",
    "resource_type",
    "capability_state",
    *_SUPPORT_FIELDS.values(),
    "requires_human_approval",
    "provider_verification_required",
}
_TOP_FIELDS = {"contract_version", "source", "capabilities"}
_SOURCE_FIELDS = {"kind", "version"}
_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$")

# Product ceilings are deliberately narrower than any private source catalog.
# M4B promotes only public-safe s3_ssl into the synthetic governed path.
_MAX_STATE = {
    "s3_ssl": "VERIFY",
    "s3_logging": "EXPLAIN",
    "s3_backup": "EXPLAIN",
    "restricted_ssh": "VERIFY",
}


class CapabilityContractError(ValueError):
    pass


def _exact_keys(value: Any, expected: set[str], error: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise CapabilityContractError(error)
    return value


def _bool(record: Mapping[str, Any], field: str) -> bool:
    value = record[field]
    if type(value) is not bool:
        raise CapabilityContractError("capability flags must be boolean")
    return value


def _derived_state(record: Mapping[str, Any]) -> str:
    enabled = [state for state in CAPABILITY_STATES if _bool(record, _SUPPORT_FIELDS[state])]
    if not enabled:
        raise CapabilityContractError("approved controls must retain DETECT capability")
    highest = CAPABILITY_STATES.index(enabled[-1])
    if enabled != list(CAPABILITY_STATES[: highest + 1]):
        raise CapabilityContractError("capability progression must be contiguous")
    return enabled[-1]


def _validate_record(raw: Any) -> dict[str, Any]:
    record = _exact_keys(raw, _RECORD_FIELDS, "capability record fields are invalid")
    control_key = record["control_key"]
    resource_type = record["resource_type"]
    if control_key not in APPROVED_CONTROLS or resource_type != APPROVED_CONTROLS[control_key]:
        raise CapabilityContractError("control or resource type is outside the public-safe registry")

    state = _derived_state(record)
    if record["capability_state"] != state:
        raise CapabilityContractError("capability_state does not match declared support")
    if CAPABILITY_STATES.index(state) > CAPABILITY_STATES.index(_MAX_STATE[control_key]):
        raise CapabilityContractError("capability exceeds the current aws-secops product path")

    approval = _bool(record, "requires_human_approval")
    verification = _bool(record, "provider_verification_required")
    if approval is not record["supports_remediate"]:
        raise CapabilityContractError("human approval metadata must match remediation support")
    if verification is not record["supports_remediate"]:
        raise CapabilityContractError("AWS service verification metadata must match remediation support")
    if control_key not in {"restricted_ssh", "s3_ssl"} and (record["supports_prepare"] or record["supports_remediate"]):
        raise CapabilityContractError("new controls cannot inherit an execution path")
    return {field: record[field] for field in sorted(_RECORD_FIELDS)}


class CapabilityCatalog:
    def __init__(self, payload: Mapping[str, Any]):
        contract = _exact_keys(payload, _TOP_FIELDS, "capability contract fields are invalid")
        if contract["contract_version"] != 1:
            raise CapabilityContractError("unsupported capability contract version")
        source = _exact_keys(contract["source"], _SOURCE_FIELDS, "capability source fields are invalid")
        if source["kind"] != "sanitized-capability-contract" or not isinstance(source["version"], str):
            raise CapabilityContractError("capability source is invalid")
        if not _VERSION.fullmatch(source["version"]):
            raise CapabilityContractError("capability source version is invalid")

        rows = contract["capabilities"]
        if not isinstance(rows, list) or len(rows) != len(APPROVED_CONTROLS):
            raise CapabilityContractError("exactly four public-safe controls are required")
        records = [_validate_record(row) for row in rows]
        by_key = {record["control_key"]: record for record in records}
        if set(by_key) != set(APPROVED_CONTROLS) or len(by_key) != len(records):
            raise CapabilityContractError("public-safe controls are missing or duplicated")

        self._source_version = source["version"]
        self._records = tuple(by_key[key] for key in sorted(by_key))

    def summary(self) -> dict[str, Any]:
        return {
            "version": 1,
            "source": {"kind": "sanitized-capability-contract", "version": self._source_version},
            "controls": deepcopy(list(self._records)),
            "read_only": True,
            "execution_authorized": False,
        }

    def decision(self, control_key: str, requested_state: str) -> dict[str, Any]:
        """Return routing metadata, never execution authorization."""

        if requested_state not in CAPABILITY_STATES:
            raise ValueError("unsupported capability state")
        record = next((row for row in self._records if row["control_key"] == control_key), None)
        if record is None:
            return {
                "control_key": "unsupported",
                "requested_state": requested_state,
                "supported": False,
                "route": "read-only-unsupported",
                "requires_human_approval": False,
                "execution_authorized": False,
            }
        supported = record[_SUPPORT_FIELDS[requested_state]]
        governed = requested_state in {"PREPARE", "REMEDIATE", "VERIFY"} and supported
        return {
            "control_key": control_key,
            "requested_state": requested_state,
            "supported": supported,
            "route": (
                "synthetic-governed-path" if governed and control_key == "s3_ssl"
                else "existing-governed-path" if governed else "read-only"
            ),
            "requires_human_approval": bool(record["requires_human_approval"] and requested_state == "REMEDIATE"),
            "execution_authorized": False,
        }


@lru_cache(maxsize=1)
def _default_catalog() -> CapabilityCatalog:
    path = Path(__file__).with_name("capabilities.public.json")
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise CapabilityContractError("default capability contract is unavailable") from exc
    return CapabilityCatalog(payload)


def current_capabilities() -> dict[str, Any]:
    return _default_catalog().summary()


def capability_decision(control_key: str, requested_state: str) -> dict[str, Any]:
    return _default_catalog().decision(control_key, requested_state)
