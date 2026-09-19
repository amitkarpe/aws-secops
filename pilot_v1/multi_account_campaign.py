"""Issue #82 multi-account S3 + SG campaign contracts.

This module contains only deterministic planning/evidence helpers. Runtime AWS
calls live in scripts/issue82_campaign.py so the read-only Harness remains
unchanged.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable

S3_CONTROL = "s3-bucket-level-public-access-prohibited"
SG_CONTROL = "restricted-ssh"
CONTROLS = (S3_CONTROL, SG_CONTROL)
ALIASES = ("lab-dev", "lab-poc", "lab-qa", "lab-sec")
REGION = "ap-southeast-1"
ADMIN_TAG = {"Key": "AccessMode", "Value": "oidc-lab-admin"}

_CONFIG_STATES = {
    "COMPLIANT",
    "NON_COMPLIANT",
    "INSUFFICIENT_DATA",
    "NOT_APPLICABLE",
    "NOT_RETURNED",
    "UNAVAILABLE",
    "PENDING",
}


@dataclass(frozen=True)
class CampaignTarget:
    alias: str
    account_id: str
    role_arn: str

    def __post_init__(self) -> None:
        if self.alias not in ALIASES:
            raise ValueError("Issue #82 target alias is not approved")
        if not re.fullmatch(r"\d{12}", self.account_id):
            raise ValueError("Issue #82 target account id is invalid")
        expected = f"arn:aws:iam::{self.account_id}:role/ChatGPTCrossAccountReadRole"
        if self.role_arn != expected:
            raise ValueError("Issue #82 target role ARN is not exact")

    @property
    def resource_ref_seed(self) -> str:
        return hashlib.sha256(f"{self.alias}:{self.account_id}".encode()).hexdigest()[:12]


def parse_targets(raw: str) -> tuple[CampaignTarget, ...]:
    try:
        rows = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("Issue #82 target configuration is invalid JSON") from exc
    if not isinstance(rows, list) or len(rows) != 4:
        raise ValueError("Issue #82 requires exactly four target accounts")
    targets = tuple(
        CampaignTarget(
            alias=row.get("alias", ""),
            account_id=row.get("account_id", ""),
            role_arn=row.get("role_arn", ""),
        )
        for row in rows
        if isinstance(row, dict) and set(row) == {"alias", "account_id", "role_arn"}
    )
    if len(targets) != 4 or tuple(target.alias for target in targets) != ALIASES:
        raise ValueError("Issue #82 target order must be lab-dev, lab-poc, lab-qa, lab-sec")
    if len({target.account_id for target in targets}) != 4:
        raise ValueError("Issue #82 target accounts must be distinct")
    return targets


def s3_bpa_compliant(value: dict[str, Any] | None) -> bool:
    if not isinstance(value, dict):
        return False
    return all(value.get(key) is True for key in (
        "BlockPublicAcls",
        "IgnorePublicAcls",
        "BlockPublicPolicy",
        "RestrictPublicBuckets",
    ))


def has_unrestricted_ssh(ip_permissions: Iterable[dict[str, Any]]) -> bool:
    for permission in ip_permissions:
        if permission.get("IpProtocol") != "tcp":
            continue
        if permission.get("FromPort") != 22 or permission.get("ToPort") != 22:
            continue
        for item in permission.get("IpRanges", []):
            if item.get("CidrIp") == "0.0.0.0/0":
                return True
    return False


def normalize_config_state(state: str | None, *, provider_compliant: bool) -> str:
    if state is None:
        return "UNAVAILABLE"
    if state not in _CONFIG_STATES:
        raise ValueError("unexpected AWS Config state")
    if provider_compliant and state == "NON_COMPLIANT":
        return "PENDING"
    return state


def batch_id(control: str, entries: Iterable[tuple[str, str]]) -> str:
    if control not in CONTROLS:
        raise ValueError("unsupported Issue #82 control")
    normalized = list(entries)
    if [alias for alias, _ in normalized] != list(ALIASES):
        raise ValueError("Issue #82 frozen batch must contain the four aliases in order")
    if any(not re.fullmatch(r"[a-f0-9]{12,64}", ref) for _, ref in normalized):
        raise ValueError("Issue #82 resource reference must be a hash")
    body = json.dumps({"control": control, "targets": normalized}, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(body.encode()).hexdigest()[:20]


def public_timeline(
    *,
    control: str,
    config_state: str,
    approved: bool,
    provider_verified: bool,
    changed: bool,
) -> list[dict[str, str]]:
    if control not in CONTROLS:
        raise ValueError("unsupported Issue #82 control")
    normalized = normalize_config_state(config_state, provider_compliant=provider_verified)
    return [
        {"stage": "Finding", "status": normalized},
        {"stage": "Investigation", "status": "BOUNDED"},
        {"stage": "Recommendation", "status": "REMEDIATE" if not provider_verified else "NO_CHANGE"},
        {"stage": "Human Decision", "status": "APPROVED" if approved else "REJECTED"},
        {"stage": "Exact Tool", "status": "CALLED" if approved and changed else "NOT_CALLED"},
        {"stage": "Provider Readback", "status": "VERIFIED" if provider_verified else "UNVERIFIED"},
        {"stage": "Config Result", "status": normalized},
    ]


def public_result(
    *,
    control: str,
    batch: str,
    aliases: Iterable[str],
    decision: str,
    mutation_count: int,
    provider_verified: bool,
    config_states: dict[str, str],
) -> dict[str, Any]:
    alias_list = list(aliases)
    if alias_list != list(ALIASES):
        raise ValueError("Issue #82 public result must contain exactly the approved aliases")
    if decision not in {"PLAN", "PREPARE", "REJECT", "APPROVE", "ALREADY_COMPLIANT"}:
        raise ValueError("invalid Issue #82 decision")
    if mutation_count < 0 or mutation_count > 4:
        raise ValueError("invalid Issue #82 mutation count")
    if set(config_states) != set(ALIASES):
        raise ValueError("Issue #82 Config evidence must cover all four aliases")
    return {
        "version": 1,
        "campaign": "issue-82-s3-sg-config-e2e",
        "control": control,
        "batch_id": batch,
        "aliases": alias_list,
        "decision": decision,
        "mutation_count": mutation_count,
        "provider_verified": provider_verified,
        "config": {alias: config_states[alias] for alias in ALIASES},
        "account_ids": "hidden-by-default",
        "resource_identifiers": "hidden-by-default",
        "oidc_session": "AccessMode=oidc-lab-admin",
        "harness_mutation": False,
    }
