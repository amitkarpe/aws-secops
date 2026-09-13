"""Exact provider-guarded reset primitives shared by operator demo preparation."""
from __future__ import annotations

from .bulk import TARGET as S3_TARGET

S3_NONCOMPLIANT = {**S3_TARGET, "BlockPublicAcls": False}
SG_COMPLIANT = {"unrestricted_ssh": False}
SG_NONCOMPLIANT = {"unrestricted_ssh": True}


def require_resettable(summary: dict) -> None:
    if not isinstance(summary, dict) or not summary.get("batch_id"):
        raise ValueError("existing batch required before reset")
    counts = summary.get("counts", {})
    if summary.get("execution_active") or any(counts.get(x, 0) for x in ("PENDING", "APPROVED", "RUNNING", "UNKNOWN")):
        raise ValueError("active, pending or uncertain batch cannot be reset")


def count_s3(provider) -> dict[str, int]:
    """Best-effort exact provider counts; read failures are UNKNOWN, never compliant."""
    compliant = noncompliant = unknown = 0
    for resource in provider.resources:
        try:
            current = provider.read(resource)
        except Exception:
            unknown += 1
        else:
            if current == S3_TARGET:
                compliant += 1
            elif current == S3_NONCOMPLIANT:
                noncompliant += 1
            else:
                unknown += 1
    return {"total": len(provider.resources), "compliant": compliant,
            "noncompliant": noncompliant, "unknown": unknown}


def reset_s3(provider) -> dict[str, int]:
    """Restore only the exact owned empty-bucket BPA demo precondition."""
    changed = already = 0
    for resource in provider.resources:
        current = provider.read(resource)
        if current == S3_NONCOMPLIANT:
            already += 1
            continue
        if current != S3_TARGET:
            raise RuntimeError("unexpected S3 provider state; reset refused")
        args = provider.guard(resource)
        provider.call(
            "s3api", "put-public-access-block", **args,
            public_access_block_configuration=S3_NONCOMPLIANT,
        )
        if provider.read(resource) != S3_NONCOMPLIANT:
            raise RuntimeError("S3 reset readback failed")
        changed += 1
    return {"total": len(provider.resources), "changed": changed, "already_noncompliant": already}


def count_sg(provider) -> dict[str, int]:
    """Best-effort exact provider counts; read failures are UNKNOWN, never compliant."""
    noncompliant = compliant = unknown = 0
    for resource in provider.resources:
        try:
            current = provider.read(resource)
        except Exception:
            unknown += 1
        else:
            if current == SG_NONCOMPLIANT:
                noncompliant += 1
            elif current == SG_COMPLIANT:
                compliant += 1
            else:
                unknown += 1
    return {"total": len(provider.resources), "noncompliant": noncompliant,
            "compliant": compliant, "unknown": unknown}


def reset_sg(provider) -> dict[str, int]:
    """Restore only TCP/22 from 0.0.0.0/0 on exact owned unattached demo SGs."""
    changed = already = 0
    permission = [{
        "IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
        "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "aws-secops restricted-ssh demo"}],
    }]
    for resource in provider.resources:
        current = provider.read(resource)
        if current == SG_NONCOMPLIANT:
            already += 1
            continue
        if current != SG_COMPLIANT:
            raise RuntimeError("unexpected SG provider state; reset refused")
        provider.guard(resource)
        client = getattr(provider, "_demo_reset_client", None)
        if client is None:
            import boto3
            from botocore.config import Config
            context = getattr(provider, "context", {})
            if context.get("profile") != "vagent" or context.get("region") != "ap-southeast-1":
                raise PermissionError("unexpected SG reset identity context")
            client = boto3.Session(profile_name="vagent").client(
                "ec2", region_name="ap-southeast-1",
                config=Config(connect_timeout=5, read_timeout=15, retries={"total_max_attempts": 1}),
            )
            provider._demo_reset_client = client
        try:
            client.authorize_security_group_ingress(GroupId=resource, IpPermissions=permission)
        except Exception as exc:
            code = getattr(exc, "response", {}).get("Error", {}).get("Code", "ProviderError")
            raise RuntimeError("SG reset provider write failed: " + code) from None
        if provider.read(resource) != SG_NONCOMPLIANT:
            raise RuntimeError("SG reset readback failed")
        changed += 1
    return {"total": len(provider.resources), "changed": changed, "already_noncompliant": already}
