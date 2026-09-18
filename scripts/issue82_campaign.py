#!/usr/bin/env python3
"""Issue #82 OIDC runtime: S3 + SG + AWS Config E2E campaign.

The caller must already hold the management GitHub OIDC controller session.
This script assumes only the four exact registered LAB target roles with the
AccessMode=oidc-lab-admin session tag. Public stdout is alias-only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

from pilot_v1.multi_account_campaign import (
    ADMIN_TAG,
    ALIASES,
    CONTROLS,
    REGION,
    S3_CONTROL,
    SG_CONTROL,
    CampaignTarget,
    batch_id,
    has_unrestricted_ssh,
    normalize_config_state,
    parse_targets,
    public_result,
    s3_bpa_compliant,
)

TARGETS_ENV = "SECOPS_ISSUE82_TARGETS_JSON"
ROLE_SESSION = "aws-secops-issue82"
TAGS = [
    {"Key": "project", "Value": "aws-secops"},
    {"Key": "purpose", "Value": "issue-82-multi-account-e2e"},
    {"Key": "owner", "Value": "amit"},
    {"Key": "environment", "Value": "lab"},
    {"Key": "phase", "Value": "issue-82"},
]


class AwsError(RuntimeError):
    pass


@dataclass
class TargetSession:
    target: CampaignTarget
    env: dict[str, str]
    bucket: str | None = None
    sg_id: str | None = None


def _run(args: list[str], *, env: dict[str, str] | None = None, allow_failure: bool = False) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["aws", "--region", REGION, *args, "--no-cli-pager"],
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {}), "AWS_PAGER": "", "AWS_MAX_ATTEMPTS": "2"},
        timeout=90,
    )
    if proc.returncode and not allow_failure:
        raise AwsError("AWS operation failed")
    return proc


def _json(args: list[str], *, env: dict[str, str] | None = None) -> dict[str, Any]:
    proc = _run([*args, "--output", "json"], env=env)
    try:
        value = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise AwsError("AWS returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise AwsError("AWS returned unexpected response")
    return value


def _text(args: list[str], *, env: dict[str, str] | None = None) -> str:
    return _run([*args, "--output", "text"], env=env).stdout.strip()


def _assume(target: CampaignTarget) -> TargetSession:
    value = _json([
        "sts", "assume-role",
        "--role-arn", target.role_arn,
        "--role-session-name", ROLE_SESSION,
        "--duration-seconds", "1800",
        "--tags", f"Key={ADMIN_TAG['Key']},Value={ADMIN_TAG['Value']}",
    ])
    creds = value.get("Credentials", {})
    env = {
        "AWS_ACCESS_KEY_ID": creds.get("AccessKeyId", ""),
        "AWS_SECRET_ACCESS_KEY": creds.get("SecretAccessKey", ""),
        "AWS_SESSION_TOKEN": creds.get("SessionToken", ""),
    }
    if not all(env.values()):
        raise AwsError("target session credentials missing")
    identity = _json(["sts", "get-caller-identity"], env=env)
    if identity.get("Account") != target.account_id:
        raise AwsError("target session identity mismatch")
    return TargetSession(target, env)


def _bucket_name(target: CampaignTarget) -> str:
    suffix = hashlib.sha256(f"issue82:{target.account_id}:{target.alias}".encode()).hexdigest()[:12]
    return f"aws-secops-issue82-{target.alias}-{suffix}"


def _sg_name(target: CampaignTarget) -> str:
    return f"aws-secops-issue82-{target.alias}"


def _tag_args(extra: list[dict[str, str]] | None = None) -> list[str]:
    pairs = TAGS + (extra or [])
    return [f"Key={item['Key']},Value={item['Value']}" for item in pairs]


def _ensure_bucket(session: TargetSession) -> str:
    bucket = _bucket_name(session.target)
    head = _run(["s3api", "head-bucket", "--bucket", bucket], env=session.env, allow_failure=True)
    if head.returncode:
        _json([
            "s3api", "create-bucket",
            "--bucket", bucket,
            "--create-bucket-configuration", f"LocationConstraint={REGION}",
        ], env=session.env)
    tagset = {"TagSet": TAGS + [{"Key": "Name", "Value": "aws-secops-issue82-demo"}]}
    _run([
        "s3api", "put-bucket-tagging",
        "--bucket", bucket,
        "--tagging", json.dumps(tagset, separators=(",", ":")),
    ], env=session.env)
    session.bucket = bucket
    return bucket


def _select_vpc(session: TargetSession) -> str:
    value = _json([
        "ec2", "describe-vpcs",
        "--filters", "Name=is-default,Values=true",
    ], env=session.env)
    rows = value.get("Vpcs", [])
    if not rows:
        value = _json(["ec2", "describe-vpcs"], env=session.env)
        rows = sorted(value.get("Vpcs", []), key=lambda row: row.get("VpcId", ""))
    if not rows or not isinstance(rows[0].get("VpcId"), str):
        raise AwsError("no VPC available for bounded demo Security Group")
    return rows[0]["VpcId"]


def _describe_demo_sgs(session: TargetSession) -> list[dict[str, Any]]:
    name = _sg_name(session.target)
    value = _json([
        "ec2", "describe-security-groups",
        "--filters",
        f"Name=group-name,Values={name}",
        "Name=tag:project,Values=aws-secops",
        "Name=tag:phase,Values=issue-82",
    ], env=session.env)
    rows = value.get("SecurityGroups", [])
    if not isinstance(rows, list):
        raise AwsError("invalid Security Group inventory response")
    return rows


def _find_bucket(session: TargetSession) -> str:
    bucket = _bucket_name(session.target)
    head = _run(["s3api", "head-bucket", "--bucket", bucket], env=session.env, allow_failure=True)
    if head.returncode:
        raise AwsError("Issue #82 demo bucket is missing; run prepare first")
    session.bucket = bucket
    return bucket


def _find_sg(session: TargetSession) -> str:
    groups = _describe_demo_sgs(session)
    if len(groups) != 1 or not isinstance(groups[0].get("GroupId"), str):
        raise AwsError("Issue #82 demo Security Group is missing or ambiguous; run prepare first")
    session.sg_id = groups[0]["GroupId"]
    return session.sg_id


def _ensure_sg(session: TargetSession) -> str:
    groups = _describe_demo_sgs(session)
    groups = value.get("SecurityGroups", [])
    if len(groups) > 1:
        raise AwsError("multiple Issue #82 demo Security Groups found")
    if groups:
        sg_id = groups[0].get("GroupId")
    else:
        vpc_id = _select_vpc(session)
        created = _json([
            "ec2", "create-security-group",
            "--group-name", name,
            "--description", "aws-secops Issue 82 unattached demo",
            "--vpc-id", vpc_id,
            "--tag-specifications",
            "ResourceType=security-group,Tags=[" + ",".join("{" + item + "}" for item in _tag_args([
                {"Key": "Name", "Value": "aws-secops-issue82-demo"}
            ])) + "]",
        ], env=session.env)
        sg_id = created.get("GroupId")
    if not isinstance(sg_id, str):
        raise AwsError("Issue #82 demo Security Group id missing")
    _run([
        "ec2", "create-tags", "--resources", sg_id, "--tags",
        *_tag_args([{"Key": "Name", "Value": "aws-secops-issue82-demo"}]),
    ], env=session.env)
    session.sg_id = sg_id
    return sg_id


def _assert_bucket_safe_for_rearm(session: TargetSession, bucket: str) -> None:
    objects = _json(["s3api", "list-objects-v2", "--bucket", bucket, "--max-keys", "1"], env=session.env)
    if objects.get("KeyCount", 0) != 0 or objects.get("Contents"):
        raise AwsError("demo bucket is not empty")
    policy = _run(["s3api", "get-bucket-policy", "--bucket", bucket], env=session.env, allow_failure=True)
    if policy.returncode == 0:
        raise AwsError("demo bucket unexpectedly has a bucket policy")
    acl = _json(["s3api", "get-bucket-acl", "--bucket", bucket], env=session.env)
    grants = acl.get("Grants", [])
    if len(grants) != 1 or grants[0].get("Permission") != "FULL_CONTROL":
        raise AwsError("demo bucket ACL is not owner-only")


def _sg_is_unattached(session: TargetSession, sg_id: str) -> bool:
    value = _json([
        "ec2", "describe-network-interfaces",
        "--filters", f"Name=group-id,Values={sg_id}",
    ], env=session.env)
    return len(value.get("NetworkInterfaces", [])) == 0


def _get_bpa(session: TargetSession, bucket: str) -> dict[str, Any] | None:
    proc = _run([
        "s3api", "get-public-access-block", "--bucket", bucket, "--output", "json"
    ], env=session.env, allow_failure=True)
    if proc.returncode:
        return None
    try:
        value = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AwsError("invalid S3 BPA response") from exc
    return value.get("PublicAccessBlockConfiguration")


def _get_sg(session: TargetSession, sg_id: str) -> dict[str, Any]:
    value = _json([
        "ec2", "describe-security-groups", "--group-ids", sg_id
    ], env=session.env)
    rows = value.get("SecurityGroups", [])
    if len(rows) != 1:
        raise AwsError("demo Security Group readback failed")
    return rows[0]


def _open_ssh_rule_ids(session: TargetSession, sg_id: str) -> list[str]:
    value = _json([
        "ec2", "describe-security-group-rules",
        "--filters", f"Name=group-id,Values={sg_id}",
    ], env=session.env)
    result: list[str] = []
    for row in value.get("SecurityGroupRules", []):
        if row.get("IsEgress"):
            continue
        if row.get("IpProtocol") != "tcp" or row.get("FromPort") != 22 or row.get("ToPort") != 22:
            continue
        if row.get("CidrIpv4") != "0.0.0.0/0":
            continue
        rule_id = row.get("SecurityGroupRuleId")
        if isinstance(rule_id, str):
            result.append(rule_id)
    return result


def _config_state(session: TargetSession, control: str, resource_id: str, provider_compliant: bool) -> str:
    recorder = _json(["configservice", "describe-configuration-recorder-status"], env=session.env)
    statuses = recorder.get("ConfigurationRecordersStatus", [])
    if not any(row.get("recording") is True and row.get("lastStatus") == "SUCCESS" for row in statuses):
        return "UNAVAILABLE"
    rules = _run([
        "configservice", "describe-config-rules",
        "--config-rule-names", control,
        "--output", "json",
    ], env=session.env, allow_failure=True)
    if rules.returncode:
        return "UNAVAILABLE"
    details = _run([
        "configservice", "get-compliance-details-by-config-rule",
        "--config-rule-name", control,
        "--limit", "100",
        "--output", "json",
    ], env=session.env, allow_failure=True)
    if details.returncode:
        return "UNAVAILABLE"
    try:
        rows = json.loads(details.stdout or "{}").get("EvaluationResults", [])
    except json.JSONDecodeError:
        return "UNAVAILABLE"
    found: str | None = None
    for row in rows:
        qualifier = row.get("EvaluationResultIdentifier", {}).get("EvaluationResultQualifier", {})
        if qualifier.get("ResourceId") == resource_id:
            found = row.get("ComplianceType")
            break
    if found is None:
        found = "NOT_RETURNED"
    return normalize_config_state(found, provider_compliant=provider_compliant)


def prepare(sessions: list[TargetSession]) -> dict[str, Any]:
    for session in sessions:
        bucket = _ensure_bucket(session)
        sg_id = _ensure_sg(session)
        _assert_bucket_safe_for_rearm(session, bucket)
        if not _sg_is_unattached(session, sg_id):
            raise AwsError("demo Security Group is attached")
        _run([
            "s3api", "put-public-access-block",
            "--bucket", bucket,
            "--public-access-block-configuration",
            "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false",
        ], env=session.env)
        rules = _open_ssh_rule_ids(session, sg_id)
        if len(rules) > 1:
            raise AwsError("demo Security Group has multiple unrestricted SSH rules")
        if not rules:
            _run([
                "ec2", "authorize-security-group-ingress",
                "--group-id", sg_id,
                "--ip-permissions",
                "IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=0.0.0.0/0,Description=aws-secops-issue82-demo}]",
            ], env=session.env)
    return {
        "campaign": "issue-82-s3-sg-config-e2e",
        "mode": "PREPARE",
        "aliases": list(ALIASES),
        "s3": "SAFE_NONCOMPLIANT",
        "sg": "SAFE_NONCOMPLIANT_UNATTACHED",
        "config": "EVIDENCE_ONLY",
        "resource_identifiers": "hidden-by-default",
    }


def _plan_for_control(sessions: list[TargetSession], control: str) -> tuple[str, list[TargetSession], dict[str, str]]:
    pending: list[TargetSession] = []
    refs: list[tuple[str, str]] = []
    config_states: dict[str, str] = {}
    for session in sessions:
        if control == S3_CONTROL:
            bucket = session.bucket or _find_bucket(session)
            provider_ok = s3_bpa_compliant(_get_bpa(session, bucket))
            resource_id = bucket
        elif control == SG_CONTROL:
            sg_id = session.sg_id or _find_sg(session)
            group = _get_sg(session, sg_id)
            if not _sg_is_unattached(session, sg_id):
                raise AwsError("demo Security Group is attached")
            provider_ok = not has_unrestricted_ssh(group.get("IpPermissions", []))
            resource_id = sg_id
        else:
            raise ValueError("unsupported control")
        if not provider_ok:
            pending.append(session)
        ref = hashlib.sha256(f"{session.target.alias}:{resource_id}".encode()).hexdigest()[:16]
        refs.append((session.target.alias, ref))
        config_states[session.target.alias] = _config_state(
            session, control, resource_id, provider_compliant=provider_ok
        )
    frozen = batch_id(control, refs)
    return frozen, pending, config_states


def plan(sessions: list[TargetSession], control: str) -> dict[str, Any]:
    frozen, pending, config_states = _plan_for_control(sessions, control)
    decision = "PLAN" if pending else "ALREADY_COMPLIANT"
    return public_result(
        control=control,
        batch=frozen,
        aliases=ALIASES,
        decision=decision,
        mutation_count=0,
        provider_verified=not pending,
        config_states=config_states,
    ) | {"pending_aliases": [s.target.alias for s in pending]}


def execute(sessions: list[TargetSession], control: str, decision: str, expected_batch: str) -> dict[str, Any]:
    frozen, pending, before_config = _plan_for_control(sessions, control)
    if frozen != expected_batch:
        raise ValueError("frozen batch id mismatch")
    if not pending:
        return public_result(
            control=control,
            batch=frozen,
            aliases=ALIASES,
            decision="ALREADY_COMPLIANT",
            mutation_count=0,
            provider_verified=True,
            config_states=before_config,
        )
    if len(pending) != 4:
        raise AwsError("Issue #82 execution requires exactly four non-compliant demo targets")
    if decision == "reject":
        return public_result(
            control=control,
            batch=frozen,
            aliases=ALIASES,
            decision="REJECT",
            mutation_count=0,
            provider_verified=False,
            config_states=before_config,
        )
    if decision != "approve":
        raise ValueError("decision must be approve or reject")

    mutation_count = 0
    for session in pending:
        if control == S3_CONTROL:
            bucket = session.bucket or _find_bucket(session)
            _run([
                "s3api", "put-public-access-block",
                "--bucket", bucket,
                "--public-access-block-configuration",
                "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true",
            ], env=session.env)
            mutation_count += 1
        else:
            sg_id = session.sg_id or _find_sg(session)
            if not _sg_is_unattached(session, sg_id):
                raise AwsError("demo Security Group is attached")
            rules = _open_ssh_rule_ids(session, sg_id)
            if len(rules) != 1:
                raise AwsError("expected exactly one unrestricted SSH demo rule")
            _run([
                "ec2", "revoke-security-group-ingress",
                "--group-id", sg_id,
                "--security-group-rule-ids", rules[0],
            ], env=session.env)
            mutation_count += 1

    _, after_pending, after_config = _plan_for_control(sessions, control)
    if after_pending:
        raise AwsError("provider readback did not prove remediation")
    return public_result(
        control=control,
        batch=frozen,
        aliases=ALIASES,
        decision="APPROVE",
        mutation_count=mutation_count,
        provider_verified=True,
        config_states=after_config,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "plan", "execute"))
    parser.add_argument("--control", choices=CONTROLS)
    parser.add_argument("--decision", choices=("approve", "reject"))
    parser.add_argument("--batch-id")
    args = parser.parse_args()

    raw = os.environ.get(TARGETS_ENV, "")
    targets = parse_targets(raw)
    sessions = [_assume(target) for target in targets]

    if args.mode == "prepare":
        result = prepare(sessions)
    elif args.mode == "plan":
        if not args.control:
            parser.error("--control is required for plan")
        result = plan(sessions, args.control)
    else:
        if not args.control or not args.decision or not args.batch_id:
            parser.error("--control, --decision and --batch-id are required for execute")
        result = execute(sessions, args.control, args.decision, args.batch_id)

    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AwsError, ValueError) as exc:
        print(f"ISSUE82_FAIL={type(exc).__name__}:{exc}", file=sys.stderr)
        raise SystemExit(65)
