"""Public-safe multi-account read-only SecOps evidence helpers.

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
ALLOWED_READS = {
    ("sts", "get-caller-identity"),
    ("configservice", "describe-compliance-by-config-rule"),
    ("ec2", "describe-vpcs"),
    ("iam", "get-account-summary"),
}


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


def _expected_arguments(service: str, operation: str) -> list[str]:
    if (service, operation) == ("sts", "get-caller-identity"):
        return []
    if (service, operation) == ("configservice", "describe-compliance-by-config-rule"):
        return ["--config-rule-names", *SUPPORTED_CONTROLS]
    if (service, operation) == ("ec2", "describe-vpcs"):
        return []
    if (service, operation) == ("iam", "get-account-summary"):
        return []
    raise ValueError("multi-account proof permits only the exact approved read operations")


def _aws_json(scope: AccountScope, service: str, operation: str, arguments: list[str]) -> dict[str, Any]:
    if (service, operation) not in ALLOWED_READS or arguments != _expected_arguments(service, operation):
        raise ValueError("multi-account proof permits only the exact approved read operations")
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


def _principal_kind(arn: str) -> str:
    if ":assumed-role/" in arn:
        return "ASSUMED_ROLE"
    if ":role/" in arn:
        return "ROLE"
    if ":user/" in arn:
        return "USER"
    if arn.endswith(":root"):
        return "ROOT"
    return "OTHER"


def read_account(scope: AccountScope, reader: Callable[[AccountScope, str, str, list[str]], dict[str, Any]] = _aws_json) -> dict[str, Any]:
    identity = reader(scope, "sts", "get-caller-identity", [])
    arn = identity.get("Arn")
    if identity.get("Account") != scope.account_id:
        raise PermissionError("configured profile does not match the expected account")
    if not isinstance(arn, str) or not arn.startswith("arn:aws:"):
        raise RuntimeError("caller identity ARN missing")
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
        "authority": "READ_ONLY_OPERATION_ALLOWLIST",
        "principal_kind": _principal_kind(arn),
        "principal_ref": hashlib.sha256(arn.encode()).hexdigest()[:10],
        "iam_scope": "RUNTIME_VERIFICATION_REQUIRED",
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
        "principal_arns": "hidden-by-default",
        "controls": list(SUPPORTED_CONTROLS),
        "mutation": False,
        "message": "Exactly two configured lab accounts were read independently through an exact operation allowlist; IAM least-privilege remains a runtime acceptance check.",
    }


def parse_overview_scopes(raw: str | None = None) -> tuple[AccountScope, ...]:
    """Accept an explicit, distinct 3-4 account read-only overview scope."""
    raw = os.environ.get(ENV_NAME, "") if raw is None else raw
    try:
        values = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("multi-account overview configuration is invalid JSON") from exc
    if not isinstance(values, list) or not 3 <= len(values) <= 4:
        raise ValueError("multi-account overview requires exactly 3-4 read-only account scopes")
    scopes: list[AccountScope] = []
    for value in values:
        if not isinstance(value, dict) or set(value) != {"label", "profile", "account_id", "region"}:
            raise ValueError("account scope requires label, profile, account_id and region only")
        label, profile, account_id, region = (value[key] for key in ("label", "profile", "account_id", "region"))
        if not isinstance(label, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,24}", label):
            raise ValueError("invalid account label")
        if not isinstance(profile, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", profile):
            raise ValueError("invalid AWS profile")
        if not isinstance(account_id, str) or not re.fullmatch(r"\d{12}", account_id):
            raise ValueError("invalid AWS account id")
        if region != "ap-southeast-1":
            raise ValueError("multi-account overview is fixed to ap-southeast-1")
        scopes.append(AccountScope(label, profile, account_id, region))
    if len({scope.label for scope in scopes}) != len(scopes):
        raise ValueError("multi-account overview account labels must be distinct")
    if len({scope.profile for scope in scopes}) != len(scopes):
        raise ValueError("multi-account overview profiles must be distinct")
    if len({scope.account_id for scope in scopes}) != len(scopes):
        raise ValueError("multi-account overview account identities must be distinct")
    return tuple(scopes)


def read_overview_account(
    scope: AccountScope,
    reader: Callable[[AccountScope, str, str, list[str]], dict[str, Any]] = _aws_json,
) -> dict[str, Any]:
    """Collect bounded, identifier-free inventory, security, and IAM evidence."""
    identity = reader(scope, "sts", "get-caller-identity", [])
    arn = identity.get("Arn")
    if identity.get("Account") != scope.account_id:
        raise PermissionError("configured profile does not match the expected account")
    if not isinstance(arn, str) or not arn.startswith("arn:aws:"):
        raise RuntimeError("caller identity ARN missing")
    controls: dict[str, str] = {control: "UNAVAILABLE" for control in SUPPORTED_CONTROLS}
    security_evidence = "CONFIG_UNAVAILABLE"
    try:
        config = reader(
            scope,
            "configservice",
            "describe-compliance-by-config-rule",
            ["--config-rule-names", *SUPPORTED_CONTROLS],
        )
        rows = config.get("ComplianceByConfigRules")
        if not isinstance(rows, list) or len(rows) > len(SUPPORTED_CONTROLS):
            raise RuntimeError("unexpected Config compliance summary")
        controls = {control: "NOT_RETURNED" for control in SUPPORTED_CONTROLS}
        for row in rows:
            if not isinstance(row, dict) or row.get("ConfigRuleName") not in SUPPORTED_CONTROLS:
                raise RuntimeError("unexpected Config rule in account summary")
            compliance = row.get("Compliance", {}).get("ComplianceType")
            if compliance not in {"COMPLIANT", "NON_COMPLIANT", "INSUFFICIENT_DATA", "NOT_APPLICABLE"}:
                raise RuntimeError("unexpected Config compliance type")
            controls[row["ConfigRuleName"]] = compliance
        security_evidence = "CONFIG_COMPLIANCE_SUMMARY"
    except RuntimeError:
        pass
    vpcs = reader(scope, "ec2", "describe-vpcs", [])
    summary = reader(scope, "iam", "get-account-summary", [])
    vpc_rows = vpcs.get("Vpcs")
    summary_map = summary.get("SummaryMap")
    if not isinstance(vpc_rows, list):
        raise RuntimeError("unexpected VPC inventory response")
    if not isinstance(summary_map, dict):
        raise RuntimeError("unexpected IAM account summary response")
    iam_counts: dict[str, int] = {}
    for key in ("Users", "Roles", "Policies"):
        value = summary_map.get(key)
        if not isinstance(value, int) or value < 0:
            raise RuntimeError("unexpected IAM account summary count")
        iam_counts[key.lower()] = value
    return {
        "label": scope.label,
        "account_ref": scope.account_ref,
        "region": scope.region,
        "controls": controls,
        "authority": "READ_ONLY_OPERATION_ALLOWLIST",
        "principal_kind": _principal_kind(arn),
        "principal_ref": hashlib.sha256(arn.encode()).hexdigest()[:10],
        "iam_scope": "RUNTIME_VERIFICATION_REQUIRED",
        "inventory": {"vpc_count": len(vpc_rows)},
        "iam": {"summary_counts": iam_counts, "evidence": "GET_ACCOUNT_SUMMARY"},
        "security": {"config_controls": controls, "evidence": security_evidence},
    }


def read_security_overview(
    raw: str | None = None,
    reader: Callable[[AccountScope, str, str, list[str]], dict[str, Any]] = _aws_json,
) -> dict[str, Any]:
    """Return a 3-4 account overview without raw account/resource identifiers."""
    accounts = [read_overview_account(scope, reader) for scope in parse_overview_scopes(raw)]
    return {
        "version": 1,
        "mode": "3-4-account-read-only-overview",
        "accounts": accounts,
        "account_ids": "hidden-by-default",
        "principal_arns": "hidden-by-default",
        "resource_identifiers": "not-collected",
        "controls": list(SUPPORTED_CONTROLS),
        "mutation": False,
        "message": "Account-distinguished inventory, Config-security, and IAM-summary evidence was collected through an exact read-only operation allowlist.",
    }


def drill_down_control(overview: dict[str, Any], account_label: str, control: str) -> dict[str, Any]:
    """Navigate overview -> account -> control without selecting a resource or mutation."""
    if control not in SUPPORTED_CONTROLS:
        raise ValueError("unsupported drill-down control")
    accounts = overview.get("accounts")
    if not isinstance(accounts, list):
        raise ValueError("invalid security overview")
    account = next((item for item in accounts if item.get("label") == account_label), None)
    if not isinstance(account, dict):
        raise ValueError("unknown overview account")
    security = account.get("security")
    if not isinstance(security, dict):
        raise ValueError("invalid drill-down evidence")
    state = security.get("config_controls", {}).get(control)
    if state not in {"COMPLIANT", "NON_COMPLIANT", "INSUFFICIENT_DATA", "NOT_APPLICABLE", "NOT_RETURNED", "UNAVAILABLE"}:
        raise ValueError("invalid drill-down evidence")
    if state == "NON_COMPLIANT":
        recommendation = "Review through the existing single-account governed remediation path; cross-account remediation is prohibited."
    elif state == "UNAVAILABLE":
        recommendation = "Investigate Config availability in the selected account; the cross-account overview cannot change it."
    else:
        recommendation = "No cross-account action is available from this read-only overview."
    return {
        "account_label": account_label,
        "account_ref": account["account_ref"],
        "control": control,
        "config_state": state,
        "evidence": security.get("evidence"),
        "resource_identifiers": "not-collected",
        "mutation": False,
        "recommendation": recommendation,
    }
