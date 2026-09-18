"""Live public-safe four-account AWS Config aggregator evidence.

The private account-id -> alias mapping is runtime-only. Browser/chat output contains
aliases and compliance states only. This module is read-only.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from typing import Any, Callable

S3_CONTROL = "s3-bucket-level-public-access-prohibited"
SG_CONTROL = "restricted-ssh"
CONTROLS = (S3_CONTROL, SG_CONTROL)
ALIASES = ("lab-dev", "lab-poc", "lab-qa", "lab-sec")
ENV_NAME = "SECOPS_MULTI_ACCOUNT_TARGETS_JSON"
AGGREGATOR = "aws-secops-issue88-org"
REGION = "ap-southeast-1"
STATES = {"COMPLIANT", "NON_COMPLIANT", "INSUFFICIENT_DATA", "NOT_APPLICABLE"}


def parse_targets(raw: str | None = None) -> dict[str, str]:
    raw = os.environ.get(ENV_NAME, "") if raw is None else raw
    try:
        values = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("four-account runtime mapping is invalid JSON") from exc
    if not isinstance(values, list) or len(values) != 4:
        raise ValueError("exactly four runtime targets are required")
    result: dict[str, str] = {}
    for row in values:
        if not isinstance(row, dict) or set(row) != {"alias", "account_id"}:
            raise ValueError("runtime target requires alias and account_id only")
        alias, account_id = row["alias"], row["account_id"]
        if alias not in ALIASES or alias in result:
            raise ValueError("unexpected or duplicate four-account alias")
        if not isinstance(account_id, str) or not re.fullmatch(r"\d{12}", account_id):
            raise ValueError("invalid runtime account id")
        result[alias] = account_id
    if tuple(result) != ALIASES or len(set(result.values())) != 4:
        raise ValueError("four-account runtime mapping must use the fixed alias order")
    return result


def _aws_aggregate() -> dict[str, Any]:
    command = [
        "aws", "configservice", "describe-aggregate-compliance-by-config-rules",
        "--configuration-aggregator-name", AGGREGATOR,
        "--region", REGION, "--output", "json", "--no-cli-pager",
    ]
    try:
        proc = subprocess.run(
            command, capture_output=True, text=True, timeout=45,
            env={**os.environ, "AWS_PAGER": "", "AWS_MAX_ATTEMPTS": "2"},
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("organization Config aggregate read timed out") from exc
    if proc.returncode:
        raise RuntimeError("organization Config aggregate read failed")
    try:
        value = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError("organization Config aggregate returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError("organization Config aggregate returned invalid response")
    return value


def _control_from_rule(name: str) -> str | None:
    for control in CONTROLS:
        if name == control or name.startswith(f"OrgConfigRule-{control}-"):
            return control
    return None


def read_status(
    raw: str | None = None,
    reader: Callable[[], dict[str, Any]] = _aws_aggregate,
) -> dict[str, Any]:
    targets = parse_targets(raw)
    reverse = {account_id: alias for alias, account_id in targets.items()}
    accounts = {
        alias: {control: "UNAVAILABLE" for control in CONTROLS}
        for alias in ALIASES
    }
    payload = reader()
    rows = payload.get("AggregateComplianceByConfigRules")
    if not isinstance(rows, list) or len(rows) > 200:
        raise RuntimeError("unexpected organization Config aggregate response")
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("unexpected organization Config aggregate row")
        alias = reverse.get(row.get("AccountId"))
        name = row.get("ConfigRuleName")
        if alias is None or not isinstance(name, str):
            continue
        control = _control_from_rule(name)
        if control is None:
            continue
        state = row.get("Compliance", {}).get("ComplianceType")
        if state not in STATES:
            raise RuntimeError("unexpected organization Config compliance state")
        accounts[alias][control] = state
    result_accounts = [
        {"alias": alias, "controls": accounts[alias]}
        for alias in ALIASES
    ]
    return {
        "version": 1,
        "scope": "four-account-live-config",
        "source": "AWS Config organization aggregator",
        "region": REGION,
        "accounts": result_accounts,
        "controls": list(CONTROLS),
        "account_ids": "hidden-by-default",
        "resource_identifiers": "not-collected",
        "mutation": False,
        "message": "Live account-level Config evidence for exactly four LAB aliases. Provider readback remains separate remediation truth.",
    }


def remediation_plan(
    control: str = "all",
    raw: str | None = None,
    reader: Callable[[], dict[str, Any]] = _aws_aggregate,
) -> dict[str, Any]:
    if control not in {"all", *CONTROLS}:
        raise ValueError("unsupported four-account control")
    status = read_status(raw, reader)
    selected = CONTROLS if control == "all" else (control,)
    plans = []
    for current in selected:
        rows = []
        for account in status["accounts"]:
            state = account["controls"][current]
            rows.append({
                "alias": account["alias"],
                "config_state": state,
                "needs_attention": state == "NON_COMPLIANT",
            })
        plans.append({
            "control": current,
            "accounts": rows,
            "noncompliant_aliases": [row["alias"] for row in rows if row["needs_attention"]],
            "execution_path": "separate governed GitHub OIDC G/O path",
            "chat_execution_available": False,
        })
    return {
        "version": 1,
        "scope": status["scope"],
        "control": control,
        "plans": plans,
        "account_ids": "hidden-by-default",
        "resource_identifiers": "not-collected",
        "mutation": False,
        "message": "Four-account planning is read-only in this chat runtime. Multi-account writes remain on the separately governed G/O path.",
    }
