"""Read-only five-control S3 baseline for an operator-owned bucket allowlist."""

from __future__ import annotations

import json
import os
from typing import Any, Callable

from .read_lambda import _tool_name


def _optional(call: Callable[[], dict[str, Any]], missing_codes: set[str]) -> dict[str, Any] | None:
    try:
        return call()
    except Exception as exc:
        code = getattr(exc, "response", {}).get("Error", {}).get("Code", "")
        if code in missing_codes:
            return None
        raise


def _secure_transport(policy: dict[str, Any] | None, bucket_arn: str) -> bool:
    if not policy:
        return False
    statements = policy.get("Statement", [])
    if isinstance(statements, dict):
        statements = [statements]
    required_resources = {bucket_arn, f"{bucket_arn}/*"}
    for statement in statements:
        actions = statement.get("Action", [])
        resources = statement.get("Resource", [])
        if isinstance(actions, str):
            actions = [actions]
        if isinstance(resources, str):
            resources = [resources]
        secure_value = statement.get("Condition", {}).get("Bool", {}).get("aws:SecureTransport")
        if (
            statement.get("Effect") == "Deny"
            and "s3:*" in actions
            and required_resources.issubset(set(resources))
            and str(secure_value).lower() == "false"
        ):
            return True
    return False


def check_s3_baseline(s3: Any, bucket: str) -> dict[str, Any]:
    public = _optional(
        lambda: s3.get_public_access_block(Bucket=bucket),
        {"NoSuchPublicAccessBlockConfiguration"},
    )
    encryption = _optional(
        lambda: s3.get_bucket_encryption(Bucket=bucket),
        {"ServerSideEncryptionConfigurationNotFoundError"},
    )
    versioning = s3.get_bucket_versioning(Bucket=bucket)
    policy_result = _optional(
        lambda: s3.get_bucket_policy(Bucket=bucket), {"NoSuchBucketPolicy"}
    )
    ownership = _optional(
        lambda: s3.get_bucket_ownership_controls(Bucket=bucket),
        {"OwnershipControlsNotFoundError", "NoSuchOwnershipControls"},
    )

    block = (public or {}).get("PublicAccessBlockConfiguration", {})
    public_ok = all(
        block.get(key) is True
        for key in ("BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets")
    )
    rules = (encryption or {}).get("ServerSideEncryptionConfiguration", {}).get("Rules", [])
    encryption_ok = any(
        rule.get("ApplyServerSideEncryptionByDefault", {}).get("SSEAlgorithm")
        in {"AES256", "aws:kms", "aws:kms:dsse"}
        for rule in rules
    )
    ownership_rules = (ownership or {}).get("OwnershipControls", {}).get("Rules", [])
    ownership_ok = any(rule.get("ObjectOwnership") == "BucketOwnerEnforced" for rule in ownership_rules)
    try:
        policy = json.loads((policy_result or {}).get("Policy", "{}"))
    except json.JSONDecodeError:
        policy = {}
    secure_transport_ok = _secure_transport(policy, f"arn:aws:s3:::{bucket}")

    controls = [
        {"name": "Block Public Access", "status": "PASS" if public_ok else "FAIL", "evidence": "all four bucket flags enabled" if public_ok else "one or more bucket flags disabled or absent"},
        {"name": "Default encryption", "status": "PASS" if encryption_ok else "FAIL", "evidence": "S3-managed or KMS encryption configured" if encryption_ok else "default encryption absent"},
        {"name": "Versioning", "status": "PASS" if versioning.get("Status") == "Enabled" else "FAIL", "evidence": versioning.get("Status", "not enabled")},
        {"name": "TLS-only bucket policy", "status": "PASS" if secure_transport_ok else "FAIL", "evidence": "HTTP denied for bucket and objects" if secure_transport_ok else "required aws:SecureTransport deny absent"},
        {"name": "Object ownership", "status": "PASS" if ownership_ok else "FAIL", "evidence": "BucketOwnerEnforced" if ownership_ok else "BucketOwnerEnforced absent"},
    ]
    compliant = all(control["status"] == "PASS" for control in controls)
    return {
        "resource_id": bucket,
        "resource_name": bucket,
        "control": "five-control S3 baseline",
        "status": "COMPLIANT" if compliant else "NON_COMPLIANT",
        "source": "AWS S3 control-plane APIs",
        "recommendation": "No action required." if compliant else "Review failed controls; this Pilot tool is read-only.",
        "controls": controls,
        "mutation": "none",
    }


def check_s3_allowlist(
    s3: Any, buckets: list[str], *, maximum: int = 5
) -> dict[str, Any]:
    if not buckets or len(buckets) > maximum or len(buckets) != len(set(buckets)):
        raise ValueError(f"S3 allowlist must contain 1 to {maximum} unique buckets")
    if any(not isinstance(bucket, str) or not bucket.strip() for bucket in buckets):
        raise ValueError("S3 allowlist contains an invalid bucket name")

    results = [check_s3_baseline(s3, bucket) for bucket in buckets]
    exceptions = [
        {
            "resource_id": result["resource_id"],
            "resource_name": result["resource_name"],
            "control": control["name"],
            "evidence": control["evidence"],
        }
        for result in results
        for control in result["controls"]
        if control["status"] == "FAIL"
    ]
    controls_checked = len(results) * 5
    return {
        "resource_id": "operator-allowlist",
        "resource_name": f"{len(results)} allowlisted demo buckets",
        "control": "five-control S3 allowlist baseline",
        "status": "NON_COMPLIANT" if exceptions else "COMPLIANT",
        "source": "AWS S3 control-plane APIs",
        "recommendation": (
            "Review only the listed failed controls; this Pilot tool is read-only."
            if exceptions
            else "No action required."
        ),
        "buckets_checked": len(results),
        "controls_checked": controls_checked,
        "pass_count": controls_checked - len(exceptions),
        "fail_count": len(exceptions),
        "buckets": [
            {
                "resource_id": result["resource_id"],
                "resource_name": result["resource_name"],
                "status": result["status"],
                "pass_count": sum(control["status"] == "PASS" for control in result["controls"]),
                "fail_count": sum(control["status"] == "FAIL" for control in result["controls"]),
            }
            for result in results
        ],
        "exceptions": exceptions,
        "mutation": "none",
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    if event != {"environment": "dev"}:
        raise ValueError("check_s3_baseline accepts only the fixed dev context")
    if _tool_name(context) != "check_s3_baseline":
        raise ValueError("unknown S3 tool")
    configured = os.environ.get("PILOT_DEMO_BUCKETS", "")
    if configured:
        try:
            buckets = json.loads(configured)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Pilot S3 allowlist is invalid") from exc
    else:
        buckets = [os.environ.get("PILOT_DEMO_BUCKET", "")]
    if not isinstance(buckets, list) or not all(isinstance(item, str) for item in buckets):
        raise RuntimeError("Pilot S3 allowlist is invalid")
    import boto3

    return check_s3_allowlist(boto3.client("s3"), buckets)
