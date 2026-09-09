"""Exact provider-backed read tools for Pilot v1."""

from __future__ import annotations

import os
from typing import Any


PUBLIC_IPV4 = "0.0.0.0/0"


def _tool_name(context: Any) -> str:
    custom = getattr(getattr(context, "client_context", None), "custom", {}) or {}
    full_name = custom.get("bedrockAgentCoreToolName", "")
    return full_name.rsplit("___", 1)[-1]


def _has_unrestricted_ssh(group: dict[str, Any]) -> bool:
    for permission in group.get("IpPermissions", []):
        protocol = permission.get("IpProtocol")
        from_port = permission.get("FromPort")
        to_port = permission.get("ToPort")
        covers_ssh = protocol == "-1" or (
            protocol == "tcp"
            and isinstance(from_port, int)
            and isinstance(to_port, int)
            and from_port <= 22 <= to_port
        )
        if covers_ssh and any(item.get("CidrIp") == PUBLIC_IPV4 for item in permission.get("IpRanges", [])):
            return True
    return False


def check_security_group(ec2: Any, group_id: str) -> dict[str, str]:
    groups = ec2.describe_security_groups(GroupIds=[group_id]).get("SecurityGroups", [])
    if len(groups) != 1 or groups[0].get("GroupId") != group_id:
        raise RuntimeError("fixed demo Security Group was not returned")
    group = groups[0]
    non_compliant = _has_unrestricted_ssh(group)
    return {
        "resource_id": group_id,
        "resource_name": group.get("GroupName", "demo-security-group"),
        "control": "TCP/22 from the public IPv4 internet",
        "status": "NON_COMPLIANT" if non_compliant else "COMPLIANT",
        "source": PUBLIC_IPV4 if non_compliant else "none",
        "recommendation": (
            "Remove the exact TCP/22 ingress rule from 0.0.0.0/0."
            if non_compliant
            else "No action required; the unrestricted SSH rule is absent."
        ),
        "mutation": "none",
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, str]:
    if event != {"environment": "dev"}:
        raise ValueError("check_security_group accepts only the fixed dev context")
    if _tool_name(context) != "check_security_group":
        raise ValueError("unknown read tool")
    group_id = os.environ.get("PILOT_DEMO_SG_ID", "")
    if not group_id:
        raise RuntimeError("fixed demo Security Group is not configured")
    import boto3

    return check_security_group(boto3.client("ec2"), group_id)
