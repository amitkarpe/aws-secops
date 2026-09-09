"""Exact Pilot v1 Security Group remediation Lambda."""

from __future__ import annotations

import os
from typing import Any

from .read_lambda import PUBLIC_IPV4, _has_unrestricted_ssh, _tool_name


EXACT_PERMISSION = {
    "IpProtocol": "tcp",
    "FromPort": 22,
    "ToPort": 22,
    "IpRanges": [{"CidrIp": PUBLIC_IPV4}],
}


def remove_unrestricted_ssh(ec2: Any, group_id: str) -> dict[str, Any]:
    before = ec2.describe_security_groups(GroupIds=[group_id])["SecurityGroups"]
    if len(before) != 1 or before[0].get("GroupId") != group_id:
        raise RuntimeError("fixed demo Security Group was not returned")
    if not _has_unrestricted_ssh(before[0]):
        return {
            "result": "ALREADY_COMPLIANT",
            "changed": False,
            "verification": "COMPLIANT",
        }
    ec2.revoke_security_group_ingress(GroupId=group_id, IpPermissions=[EXACT_PERMISSION])
    after = ec2.describe_security_groups(GroupIds=[group_id])["SecurityGroups"]
    if len(after) != 1 or _has_unrestricted_ssh(after[0]):
        raise RuntimeError("provider verification did not confirm remediation")
    return {
        "result": "SSH_RULE_REMOVED",
        "changed": True,
        "verification": "COMPLIANT",
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    if event != {"environment": "dev", "approved": True}:
        raise ValueError("remediation requires the fixed dev approval context")
    if _tool_name(context) != "remove_unrestricted_ssh":
        raise ValueError("unknown remediation tool")
    group_id = os.environ.get("PILOT_DEMO_SG_ID", "")
    if not group_id:
        raise RuntimeError("fixed demo Security Group is not configured")
    import boto3

    return remove_unrestricted_ssh(boto3.client("ec2"), group_id)
