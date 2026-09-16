"""Exactly-two-account read-only Config proof for the agentic SecOps next phase.

No roles are created here and no write API is available. Account configuration
comes from an operator-owned environment value and is validated before any AWS
CLI read occurs.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Callable

S3_CONTROL = "s3-bucket-level-public-access-prohibited"
SG_CONTROL = "restricted-ssh"
SUPPORTED_CONTROLS = (S3_CONTROL, SG_CONTROL)
ENV_NAME = "SECOPS_READ_ACCOUNTS_JSON"


@dataclass(frozen=True)
class AccountScope:
    label: str
    profile: str
    account_id: str
    region: str = "ap-southeast-1"

    @property
    def account_ref(self) -> str:
        digest = hashlib.sha256(self.account_id.encode()).hexdigest()[:10]
        return f"{self.label}:{digest}"


def parse_scopes(raw: str | None = None) -> tuple[AccountScope, AccountScope]:
    raw = os.environ.get(ENV_NAME, "") if raw is None else raw
    try:
        values = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("two-account read configuration is invalid JSON") from exc
    if not isinstance(values, list) or len(values) != 2:
        raise ValueError("exactly two read-only account scopes are required")
    scopes: list[AccountScope] = []
    for value in values:
        if not isinstance(value, dict) or set(value) != {"label", "profile", "account_id", "region"}:
            raise ValueError("account scope requires label, profile, account_id and region only")
        label = value["label"]
        profile = value["profile"]
        account_id = value["account_id"]
        region = value["region"]
        if not isinstance(label, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,24}", label):
            raise ValueError("invalid account label")
        if not isinstance(profile, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", profile):
            raise ValueError("invalid AWS profile")
        if not isinstance(account_id, str) or not re.fullmatch(r"\d{12}", account_id):
            raise ValueError("invalid AWS account id")
        if region != "ap-southeast-1":
            raise ValueError("two-account proof is fixed to ap-southeast-1")
        scopes.append(AccountScope(label, profile, account_id, region))
    if scopes[0].label == scopes[1].label or scopes[0].profile == scopes[1].profile or scopes[0].account_id == scopes[1].account_id:
        raise ValueError("two distinct account scopes are required")
    return scopes[0], scopes[1]


def _aws_json(scope: AccountScope, service: str, operation: str, arguments: list[str]) -> dict[str, Any]:
    if not operation.startswith(("get-", "list-", "describe-")):
        raise ValueError("multi-account proof permits read operations only")
    command = [
        "aws", "--profile", scope.profile, "--region", scope.region,
        "--cli-connect-timeout", "10", "--cli-read-timeout", "30",
        service, operation, *arguments, "--output", "json", "--no-cli-pager",
    ]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=45,
            env={**os.environ, "AWS_MAX_ATTEMPTS": "1", "AWS_PAGER": ""},
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("read-only account query timed out") from exc
    if result.returncode:
        raise RuntimeError("read-only account query failed")
    try:
        value = json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError("read-only account query returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError("read-only account query returned invalid response")
    return value


def read_account(scope: AccountScope, reader: Callable[[AccountScope, str, str, list[str]], dict[str, Any]] = _aws_json) -> dict[str, Any]:
    identity = reader(scope, "sts", "get-caller-identity", [])
    if identity.get("Account") != scope.account_id:
        raise PermissionError("configured profile does not match the expected account")
    result = reader(
        scope,
        "configservice",
        "describe-compliance-by-config-rule",
        ["--config-rule-names", *SUPPORTED_CONTROLS],
    )
    rows = result.get("ComplianceByConfigRules")
    if not isinstance(rows, list) or len(rows) > len(SUPPORTED_CONTROLS):
        raise RuntimeError("unexpected Config compliance summary")
    controls: dict[str, str] = {control: "NOT_RETURNED" for control in SUPPORTED_CONTROLS}
    for row in rows:
        if not isinstance(row, dict) or row.get("ConfigRuleName") not in SUPPORTED_CONTROLS:
            raise RuntimeError("unexpected Config rule in account summary")
        compliance = row.get("Compliance", {}).get("ComplianceType")
        if compliance not in {"COMPLIANT", "NON_COMPLIANT", "INSUFFICIENT_DATA", "NOT_APPLICABLE"}:
            raise RuntimeError("unexpected Config compliance type")
        controls[row["ConfigRuleName"]] = compliance
    return {
        "label": scope.label,
        "account_ref": scope.account_ref,
        "region": scope.region,
        "controls": controls,
        "authority": "READ_ONLY",
    }


def read_two_accounts(
    raw: str | None = None,
    reader: Callable[[AccountScope, str, str, list[str]], dict[str, Any]] = _aws_json,
) -> dict[str, Any]:
    scopes = parse_scopes(raw)
    accounts = [read_account(scope, reader) for scope in scopes]
    return {
        "version": 1,
        "mode": "two-account-read-only",
        "accounts": accounts,
        "account_ids": "hidden-by-default",
        "controls": list(SUPPORTED_CONTROLS),
        "mutation": False,
        "message": "Exactly two configured lab accounts were read independently; no cross-account write path exists in this proof.",
    }
