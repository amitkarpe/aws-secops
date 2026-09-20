"""Bounded CodeBuild bridge for the four-account SecOps executor.

This module starts only one fixed CodeBuild project and accepts only the two
supported controls plus a frozen batch id. It never accepts source, buildspec,
role, account, Region, repository, branch, or arbitrary environment overrides.
"""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import time
from typing import Any

from .multi_account_campaign import S3_CONTROL, SG_CONTROL

PROJECT = "aws-secops-four-account-executor"
REGION = "ap-southeast-1"
CONTROLS = {S3_CONTROL, SG_CONTROL}
BATCH_RE = re.compile(r"^[a-f0-9]{20}$")
TERMINAL = {"SUCCEEDED", "FAILED", "FAULT", "STOPPED", "TIMED_OUT"}


class BuildError(RuntimeError):
    pass


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.pop("AWS_PROFILE", None)
    env.pop("AWS_DEFAULT_PROFILE", None)
    env.update({"AWS_PAGER": "", "AWS_MAX_ATTEMPTS": "2"})
    proc = subprocess.run(
        ["aws", "--region", REGION, *args, "--no-cli-pager"],
        capture_output=True,
        text=True,
        env=env,
        timeout=45,
    )
    if proc.returncode:
        raise BuildError("bounded CodeBuild operation failed")
    return proc


def _json(args: list[str]) -> dict[str, Any]:
    proc = _run([*args, "--output", "json"])
    try:
        value = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise BuildError("CodeBuild returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise BuildError("CodeBuild returned unexpected response")
    return value


def _validate(mode: str, control: str, batch_id: str | None, exclusions: list[str]) -> None:
    if mode not in {"prepare", "plan", "execute"}:
        raise ValueError("unsupported execution mode")
    if control not in CONTROLS:
        raise ValueError("unsupported control")
    if mode in {"prepare", "plan"}:
        if batch_id is not None:
            raise ValueError(mode + " does not accept a batch id")
    else:
        if not isinstance(batch_id, str) or not BATCH_RE.fullmatch(batch_id):
            raise ValueError("exact frozen batch id required")
    if len(exclusions) > 3 or len(exclusions) != len(set(exclusions)):
        raise ValueError("invalid exact one-time exclusions")
    if any(not isinstance(value, str) or not value or len(value) > 255 or any(ch in value for ch in "*?[]") for value in exclusions):
        raise ValueError("invalid exact one-time exclusion")


def run(
    mode: str,
    control: str,
    batch_id: str | None = None,
    *,
    exclusions: list[str] | None = None,
    timeout: int = 150,
) -> dict[str, Any]:
    exclusions = list(exclusions or [])
    _validate(mode, control, batch_id, exclusions)
    overrides = [
        {"name": "SECOPS_MODE", "value": mode, "type": "PLAINTEXT"},
        {"name": "SECOPS_CONTROL", "value": control, "type": "PLAINTEXT"},
    ]
    if batch_id is not None:
        overrides.append({"name": "SECOPS_BATCH_ID", "value": batch_id, "type": "PLAINTEXT"})
    if exclusions:
        overrides.append({
            "name": "SECOPS_EXCLUDE_RESOURCES_JSON",
            "value": json.dumps(exclusions, separators=(",", ":")),
            "type": "PLAINTEXT",
        })

    started = _json([
        "codebuild", "start-build",
        "--project-name", PROJECT,
        "--environment-variables-override", json.dumps(overrides, separators=(",", ":")),
    ])
    build_id = started.get("build", {}).get("id")
    if not isinstance(build_id, str) or not build_id.startswith(PROJECT + ":"):
        raise BuildError("unexpected CodeBuild start response")

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = _json(["codebuild", "batch-get-builds", "--ids", build_id])
        builds = value.get("builds", [])
        if len(builds) != 1:
            raise BuildError("CodeBuild status unavailable")
        build = builds[0]
        status = build.get("buildStatus")
        if status not in TERMINAL:
            time.sleep(2)
            continue
        if status != "SUCCEEDED":
            raise BuildError("bounded CodeBuild execution failed")
        exported = {
            row.get("name"): row.get("value")
            for row in build.get("exportedEnvironmentVariables", [])
            if isinstance(row, dict)
        }
        encoded = exported.get("SECOPS_RESULT_B64")
        if not isinstance(encoded, str) or not encoded:
            raise BuildError("CodeBuild result was not exported")
        try:
            raw = base64.b64decode(encoded, validate=True)
            result = json.loads(raw)
        except Exception as exc:
            raise BuildError("CodeBuild result was invalid") from exc
        if not isinstance(result, dict):
            raise BuildError("CodeBuild result was not an object")
        if result.get("control") != control or result.get("batch_id") is None:
            raise BuildError("CodeBuild result scope mismatch")
        if result.get("account_ids") != "hidden-by-default" or result.get("resource_identifiers") != "hidden-by-default":
            raise BuildError("CodeBuild result violated public-safe boundary")
        response = dict(result)
        response["build_status"] = "SUCCEEDED"
        response["execution_backend"] = "AWS CodeBuild via GitHub CodeConnections"
        response["build_id"] = "hidden-by-default"
        return response
    raise BuildError("bounded CodeBuild execution timed out")
