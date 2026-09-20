#!/usr/bin/env python3
"""CodeBuild entry point for Issue #100.

The CodeBuild service role may assume only the existing G/O controller role.
That controller role then uses the already-proven issue82 campaign logic.
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys

from pilot_v1.multi_account_campaign import ALIASES, S3_CONTROL, SG_CONTROL

CONTROLLER_ENV = "SECOPS_CONTROLLER_ROLE_ARN"
TARGETS_ENV = "SECOPS_ISSUE82_TARGETS_JSON"
CONTROLS = {S3_CONTROL, SG_CONTROL}
BATCH_RE = re.compile(r"^[a-f0-9]{20}$")
EXCLUSIONS_ENV = "SECOPS_EXCLUDE_RESOURCES_JSON"


def fail(message: str) -> None:
    print("SECOPS_CODEBUILD_FAIL=" + message, file=sys.stderr)
    raise SystemExit(65)


def run_json(args: list[str], env: dict[str, str] | None = None) -> dict:
    proc = subprocess.run(
        args,
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {}), "AWS_PAGER": "", "AWS_MAX_ATTEMPTS": "2"},
        timeout=120,
    )
    if proc.returncode:
        fail("bounded subprocess failed")
    try:
        value = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        fail("bounded subprocess returned invalid JSON")
    if not isinstance(value, dict):
        fail("bounded subprocess returned unexpected response")
    return value


def controller_env() -> dict[str, str]:
    arn = os.environ.get(CONTROLLER_ENV, "")
    if not arn.endswith(":role/github-actions-aws-platform-lab-read-controller"):
        fail("controller role scope invalid")
    value = run_json([
        "aws", "sts", "assume-role",
        "--role-arn", arn,
        "--role-session-name", "aws-secops-codebuild-issue100",
        "--duration-seconds", "900",
        "--output", "json",
        "--no-cli-pager",
    ])
    creds = value.get("Credentials", {})
    result = {
        "AWS_ACCESS_KEY_ID": creds.get("AccessKeyId", ""),
        "AWS_SECRET_ACCESS_KEY": creds.get("SecretAccessKey", ""),
        "AWS_SESSION_TOKEN": creds.get("SessionToken", ""),
    }
    if not all(result.values()):
        fail("controller credentials missing")
    return result


def main() -> int:
    mode = os.environ.get("SECOPS_MODE", "")
    control = os.environ.get("SECOPS_CONTROL", "")
    batch_id = os.environ.get("SECOPS_BATCH_ID")
    raw_exclusions = os.environ.get(EXCLUSIONS_ENV, "[]")

    if mode not in {"prepare", "plan", "execute"} or control not in CONTROLS:
        fail("unsupported request")
    if mode in {"prepare", "plan"}:
        if batch_id:
            fail(mode + " must not include batch id")
    elif not isinstance(batch_id, str) or not BATCH_RE.fullmatch(batch_id):
        fail("execute requires exact batch id")

    try:
        exclusions = json.loads(raw_exclusions)
    except json.JSONDecodeError:
        fail("exclusion mapping invalid")
    if (not isinstance(exclusions, list) or len(exclusions) > 3 or len(exclusions) != len(set(exclusions))
            or any(not isinstance(x, str) or not x or len(x) > 255 or any(ch in x for ch in "*?[]") for x in exclusions)):
        fail("exact exclusion mapping invalid")

    raw_targets = os.environ.get(TARGETS_ENV, "")
    try:
        targets = json.loads(raw_targets)
    except json.JSONDecodeError:
        fail("target mapping invalid")
    if not isinstance(targets, list) or [x.get("alias") for x in targets if isinstance(x, dict)] != list(ALIASES):
        fail("exact four target aliases required")

    env = controller_env()
    env[TARGETS_ENV] = raw_targets
    command = [
        sys.executable, "scripts/issue82_campaign.py", mode,
        "--control", control,
    ]
    for resource in exclusions:
        command += ["--exclude-resource", resource]
    if mode == "execute":
        command += ["--decision", "approve", "--batch-id", batch_id or ""]

    result = run_json(command, env=env)
    if result.get("control") != control or result.get("aliases") != list(ALIASES):
        fail("campaign result scope mismatch")
    if result.get("account_ids") != "hidden-by-default" or result.get("resource_identifiers") != "hidden-by-default":
        fail("campaign result violated public-safe boundary")
    if mode == "plan" and result.get("mutation_count") != 0:
        fail("plan unexpectedly mutated")
    if mode in {"plan", "execute"} and result.get("excluded_count") != len(exclusions):
        fail("campaign exclusion scope mismatch")
    if mode == "prepare":
        if result.get("decision") != "PREPARE" or result.get("provider_verified") is not True:
            fail("unexpected prepare result")
        if not isinstance(result.get("mutation_count"), int) or not 0 <= result["mutation_count"] <= 4:
            fail("unexpected prepare mutation count")
    if mode == "execute" and result.get("decision") not in {"APPROVE", "ALREADY_COMPLIANT"}:
        fail("unexpected execution decision")
    encoded = base64.b64encode(json.dumps(result, sort_keys=True, separators=(",", ":")).encode()).decode()
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
