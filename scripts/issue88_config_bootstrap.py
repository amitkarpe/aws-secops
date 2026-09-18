#!/usr/bin/env python3
"""Issue #88 organization-wide AWS Config bootstrap for the four LAB aliases.

The caller must already hold the management GitHub OIDC controller session.
All AWS mutations use the existing AccessMode=oidc-lab-admin target sessions.
Public stdout is alias-only and never emits account IDs, ARNs, bucket names, or credentials.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

from pilot_v1.multi_account_campaign import ALIASES, REGION, CampaignTarget, parse_targets

TARGETS_ENV = "SECOPS_ISSUE82_TARGETS_JSON"
ROLE_NAME = "ChatGPTCrossAccountReadRole"
ADMIN_TAG = "Key=AccessMode,Value=oidc-lab-admin"
RECORDER_NAME = "aws-secops-issue88-recorder"
DELIVERY_NAME = "aws-secops-issue88-delivery"
AGGREGATOR_NAME = "aws-secops-issue88-org"
AGGREGATOR_ROLE = "aws-secops-issue88-config-aggregator"
S3_RULE = "s3-bucket-level-public-access-prohibited"
SG_RULE = "restricted-ssh"
S3_RULE_ID = "S3_BUCKET_LEVEL_PUBLIC_ACCESS_PROHIBITED"
SG_RULE_ID = "INCOMING_SSH_DISABLED"


class AwsError(RuntimeError):
    pass


@dataclass
class TargetSession:
    target: CampaignTarget
    env: dict[str, str]


def _run(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    allow_failure: bool = False,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["aws", "--region", REGION, *args, "--no-cli-pager"],
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {}), "AWS_PAGER": "", "AWS_MAX_ATTEMPTS": "2"},
        timeout=120,
    )
    if proc.returncode and not allow_failure:
        raise AwsError("AWS operation failed")
    return proc


def _json(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    allow_failure: bool = False,
) -> dict[str, Any]:
    proc = _run([*args, "--output", "json"], env=env, allow_failure=allow_failure)
    if proc.returncode:
        return {}
    try:
        value = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise AwsError("AWS returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise AwsError("AWS returned unexpected response")
    return value


def _call(
    service: str,
    operation: str,
    payload: dict[str, Any],
    *,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    return _json(
        [service, operation, "--cli-input-json", json.dumps(payload, separators=(",", ":"))],
        env=env,
    )


def _assume(role_arn: str, account_id: str, session_name: str) -> dict[str, str]:
    value = _json([
        "sts",
        "assume-role",
        "--role-arn",
        role_arn,
        "--role-session-name",
        session_name,
        "--duration-seconds",
        "1800",
        "--tags",
        ADMIN_TAG,
    ])
    creds = value.get("Credentials", {})
    env = {
        "AWS_ACCESS_KEY_ID": creds.get("AccessKeyId", ""),
        "AWS_SECRET_ACCESS_KEY": creds.get("SecretAccessKey", ""),
        "AWS_SESSION_TOKEN": creds.get("SessionToken", ""),
    }
    if not all(env.values()):
        raise AwsError("assumed session credentials missing")
    identity = _json(["sts", "get-caller-identity"], env=env)
    if identity.get("Account") != account_id:
        raise AwsError("assumed session identity mismatch")
    return env


def _member_sessions(targets: tuple[CampaignTarget, ...]) -> list[TargetSession]:
    return [
        TargetSession(
            target,
            _assume(target.role_arn, target.account_id, "aws-secops-issue88-config"),
        )
        for target in targets
    ]


def _management_admin() -> tuple[str, dict[str, str]]:
    identity = _json(["sts", "get-caller-identity"])
    account_id = identity.get("Account")
    if not isinstance(account_id, str) or len(account_id) != 12:
        raise AwsError("management account identity unavailable")
    role_arn = f"arn:aws:iam::{account_id}:role/{ROLE_NAME}"
    return account_id, _assume(role_arn, account_id, "aws-secops-issue88-management")


def _organization_id(env: dict[str, str]) -> str:
    value = _json(["organizations", "describe-organization"], env=env)
    org_id = value.get("Organization", {}).get("Id")
    if not isinstance(org_id, str) or not org_id.startswith("o-"):
        raise AwsError("organization id unavailable")
    return org_id


def _bucket_name(management_account: str, org_id: str) -> str:
    suffix = hashlib.sha256(
        f"issue88:{management_account}:{org_id}:{REGION}".encode()
    ).hexdigest()[:20]
    return f"aws-secops-config-org-{suffix}"


def _ensure_central_bucket(
    management_env: dict[str, str],
    management_account: str,
    org_id: str,
) -> str:
    bucket = _bucket_name(management_account, org_id)
    head = _run(["s3api", "head-bucket", "--bucket", bucket], env=management_env, allow_failure=True)
    if head.returncode:
        _call(
            "s3api",
            "create-bucket",
            {
                "Bucket": bucket,
                "CreateBucketConfiguration": {"LocationConstraint": REGION},
            },
            env=management_env,
        )

    _call(
        "s3api",
        "put-public-access-block",
        {
            "Bucket": bucket,
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        },
        env=management_env,
    )
    _call(
        "s3api",
        "put-bucket-tagging",
        {
            "Bucket": bucket,
            "Tagging": {
                "TagSet": [
                    {"Key": "project", "Value": "aws-secops"},
                    {"Key": "purpose", "Value": "issue-88-config-delivery"},
                    {"Key": "owner", "Value": "amit"},
                    {"Key": "environment", "Value": "lab"},
                    {"Key": "phase", "Value": "issue-88"},
                ]
            },
        },
        env=management_env,
    )

    bucket_arn = f"arn:aws:s3:::{bucket}"
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AWSConfigBucketPermissionsCheck",
                "Effect": "Allow",
                "Principal": {"Service": "config.amazonaws.com"},
                "Action": "s3:GetBucketAcl",
                "Resource": bucket_arn,
            },
            {
                "Sid": "AWSConfigBucketExistenceCheck",
                "Effect": "Allow",
                "Principal": {"Service": "config.amazonaws.com"},
                "Action": "s3:ListBucket",
                "Resource": bucket_arn,
            },
            {
                "Sid": "AWSConfigBucketDelivery",
                "Effect": "Allow",
                "Principal": {"Service": "config.amazonaws.com"},
                "Action": "s3:PutObject",
                "Resource": f"{bucket_arn}/AWSLogs/*/Config/*",
                "Condition": {
                    "StringEquals": {
                        "aws:SourceOrgID": org_id,
                        "s3:x-amz-acl": "bucket-owner-full-control",
                    }
                },
            },
        ],
    }
    _call(
        "s3api",
        "put-bucket-policy",
        {"Bucket": bucket, "Policy": json.dumps(policy, separators=(",", ":"))},
        env=management_env,
    )
    return bucket


def _ensure_service_linked_role(session: TargetSession) -> str:
    role = _json(
        ["iam", "get-role", "--role-name", "AWSServiceRoleForConfig"],
        env=session.env,
        allow_failure=True,
    )
    if not role:
        _json(
            [
                "iam",
                "create-service-linked-role",
                "--aws-service-name",
                "config.amazonaws.com",
            ],
            env=session.env,
        )
    return (
        f"arn:aws:iam::{session.target.account_id}:role/"
        "aws-service-role/config.amazonaws.com/AWSServiceRoleForConfig"
    )


def _ensure_member_config(session: TargetSession, bucket: str) -> None:
    role_arn = _ensure_service_linked_role(session)
    _call(
        "configservice",
        "put-configuration-recorder",
        {
            "ConfigurationRecorder": {
                "name": RECORDER_NAME,
                "roleARN": role_arn,
                "recordingGroup": {
                    "allSupported": False,
                    "includeGlobalResourceTypes": False,
                    "resourceTypes": ["AWS::S3::Bucket", "AWS::EC2::SecurityGroup"],
                    "recordingStrategy": {"useOnly": "INCLUSION_BY_RESOURCE_TYPES"},
                },
            }
        },
        env=session.env,
    )
    _call(
        "configservice",
        "put-delivery-channel",
        {
            "DeliveryChannel": {
                "name": DELIVERY_NAME,
                "s3BucketName": bucket,
                "configSnapshotDeliveryProperties": {
                    "deliveryFrequency": "TwentyFour_Hours"
                },
            }
        },
        env=session.env,
    )
    _call(
        "configservice",
        "start-configuration-recorder",
        {"ConfigurationRecorderName": RECORDER_NAME},
        env=session.env,
    )

    recorders = _json(["configservice", "describe-configuration-recorders"], env=session.env)
    channels = _json(["configservice", "describe-delivery-channels"], env=session.env)
    statuses = _json(
        ["configservice", "describe-configuration-recorder-status"], env=session.env
    )
    if not any(row.get("name") == RECORDER_NAME for row in recorders.get("ConfigurationRecorders", [])):
        raise AwsError("member Config recorder verification failed")
    if not any(row.get("name") == DELIVERY_NAME for row in channels.get("DeliveryChannels", [])):
        raise AwsError("member Config delivery verification failed")
    if not any(
        row.get("name") == RECORDER_NAME and row.get("recording") is True
        for row in statuses.get("ConfigurationRecordersStatus", [])
    ):
        raise AwsError("member Config recorder did not start")


def _ensure_aggregator_role(management_env: dict[str, str], management_account: str) -> str:
    value = _json(
        ["iam", "get-role", "--role-name", AGGREGATOR_ROLE],
        env=management_env,
        allow_failure=True,
    )
    if not value:
        trust = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "config.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }
            ],
        }
        _call(
            "iam",
            "create-role",
            {
                "RoleName": AGGREGATOR_ROLE,
                "Path": "/service-role/",
                "Description": "AWS Config organization aggregator for aws-secops Issue 88",
                "AssumeRolePolicyDocument": json.dumps(trust, separators=(",", ":")),
            },
            env=management_env,
        )
    _call(
        "iam",
        "attach-role-policy",
        {
            "RoleName": AGGREGATOR_ROLE,
            "PolicyArn": "arn:aws:iam::aws:policy/service-role/AWSConfigRoleForOrganizations",
        },
        env=management_env,
    )
    return (
        f"arn:aws:iam::{management_account}:role/service-role/{AGGREGATOR_ROLE}"
    )


def _active_org_accounts(management_env: dict[str, str]) -> list[str]:
    value = _json(["organizations", "list-accounts"], env=management_env)
    result: list[str] = []
    for row in value.get("Accounts", []):
        account_id = row.get("Id")
        state = row.get("State") or row.get("Status")
        if isinstance(account_id, str) and state == "ACTIVE":
            result.append(account_id)
    return result


def _ensure_org_rules(
    management_env: dict[str, str],
    management_account: str,
    targets: tuple[CampaignTarget, ...],
) -> None:
    for service_principal in (
        "config.amazonaws.com",
        "config-multiaccountsetup.amazonaws.com",
    ):
        _call(
            "organizations",
            "enable-aws-service-access",
            {"ServicePrincipal": service_principal},
            env=management_env,
        )

    target_ids = {target.account_id for target in targets}
    excluded = sorted(
        account_id
        for account_id in _active_org_accounts(management_env)
        if account_id not in target_ids
    )
    common_tags = [
        {"Key": "project", "Value": "aws-secops"},
        {"Key": "purpose", "Value": "issue-88-config-evidence"},
        {"Key": "owner", "Value": "amit"},
        {"Key": "environment", "Value": "lab"},
    ]

    _call(
        "configservice",
        "put-organization-config-rule",
        {
            "OrganizationConfigRuleName": S3_RULE,
            "ExcludedAccounts": excluded,
            "OrganizationManagedRuleMetadata": {
                "RuleIdentifier": S3_RULE_ID,
                "ResourceTypesScope": ["AWS::S3::Bucket"],
            },
            "Tags": common_tags,
        },
        env=management_env,
    )
    _call(
        "configservice",
        "put-organization-config-rule",
        {
            "OrganizationConfigRuleName": SG_RULE,
            "ExcludedAccounts": excluded,
            "OrganizationManagedRuleMetadata": {
                "RuleIdentifier": SG_RULE_ID,
                "ResourceTypesScope": ["AWS::EC2::SecurityGroup"],
            },
            "Tags": common_tags,
        },
        env=management_env,
    )


def _ensure_aggregator(
    management_env: dict[str, str],
    management_account: str,
) -> None:
    role_arn = _ensure_aggregator_role(management_env, management_account)
    _call(
        "configservice",
        "put-configuration-aggregator",
        {
            "ConfigurationAggregatorName": AGGREGATOR_NAME,
            "OrganizationAggregationSource": {
                "RoleArn": role_arn,
                "AwsRegions": [REGION],
                "AllAwsRegions": False,
            },
        },
        env=management_env,
    )
    value = _json(
        [
            "configservice",
            "describe-configuration-aggregators",
            "--configuration-aggregator-names",
            AGGREGATOR_NAME,
        ],
        env=management_env,
    )
    if len(value.get("ConfigurationAggregators", [])) != 1:
        raise AwsError("organization Config aggregator verification failed")


def bootstrap(targets: tuple[CampaignTarget, ...]) -> dict[str, Any]:
    management_account, management_env = _management_admin()
    org_id = _organization_id(management_env)
    bucket = _ensure_central_bucket(management_env, management_account, org_id)

    sessions = _member_sessions(targets)
    for session in sessions:
        _ensure_member_config(session, bucket)

    _ensure_org_rules(management_env, management_account, targets)
    _ensure_aggregator(management_env, management_account)

    return {
        "campaign": "issue-88-org-config-bootstrap",
        "mode": "CONFIG_BOOTSTRAP",
        "aliases": list(ALIASES),
        "member_recorders": "STARTED",
        "delivery": "CENTRAL_ORG_BUCKET",
        "organization_rules": [S3_RULE, SG_RULE],
        "aggregator": "CONFIGURED",
        "config_remediation": False,
        "scp_change": False,
        "resource_identifiers": "hidden-by-default",
        "account_ids": "hidden-by-default",
    }


def main() -> int:
    raw = os.environ.get(TARGETS_ENV, "")
    targets = parse_targets(raw)
    result = bootstrap(targets)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AwsError, ValueError) as exc:
        print(f"ISSUE88_FAIL={type(exc).__name__}:{exc}", file=sys.stderr)
        raise SystemExit(65)
