"""Gateway-only exact Security Group restricted-SSH remediation target.

The private scope manifest is packaged at deployment. This function accepts one
manifest index, re-checks ownership/unattached state and revokes only the exact
TCP/22 0.0.0.0/0 rule. No generic EC2 mutation exists.
"""
import json
from pathlib import Path
import re


def _exact_rule(rule):
    return (not rule.get("IsEgress") and rule.get("IpProtocol") == "tcp"
            and rule.get("FromPort") == 22 and rule.get("ToPort") == 22
            and rule.get("CidrIpv4") == "0.0.0.0/0" and not rule.get("CidrIpv6"))


def remediate(ec2, manifest, event):
    if (set(event) != {"scope_hash", "resource_index", "batch_id", "environment"}
            or event["environment"] != "dev" or event["scope_hash"] != manifest["scope_hash"]
            or type(event["resource_index"]) is not int
            or not 0 <= event["resource_index"] < len(manifest["security_groups"])
            or not isinstance(event["batch_id"], str)
            or not re.fullmatch("[a-f0-9]{64}", event["batch_id"])):
        raise ValueError("outside exact governed SG scope")
    entry = manifest["security_groups"][event["resource_index"]]
    group_id = entry["group_id"]
    groups = ec2.describe_security_groups(GroupIds=[group_id]).get("SecurityGroups", [])
    if len(groups) != 1:
        raise ValueError("SG unavailable")
    group = groups[0]
    if group.get("VpcId") != manifest["vpc_id"] or group.get("GroupName") != entry["name"]:
        raise ValueError("SG identity mismatch")
    tags = {x.get("Key"): x.get("Value") for x in group.get("Tags", [])}
    required = {"project": "aws-secops", "owner": "amit", "phase": "bulk-ssh", "run": manifest["run"]}
    if any(tags.get(k) != v for k, v in required.items()):
        raise ValueError("SG ownership mismatch")
    attached = ec2.describe_network_interfaces(Filters=[{"Name": "group-id", "Values": [group_id]}], MaxResults=100)
    if attached.get("NetworkInterfaces") or attached.get("NextToken"):
        raise ValueError("SG attached; no mutation")
    response = ec2.describe_security_group_rules(Filters=[{"Name": "group-id", "Values": [group_id]}])
    if response.get("NextToken"):
        raise ValueError("unexpected rule pagination")
    ingress = [x for x in response.get("SecurityGroupRules", []) if not x.get("IsEgress")]
    exact = [x for x in ingress if _exact_rule(x)]
    if len(exact) > 1 or any(x not in exact for x in ingress):
        raise ValueError("unexpected ingress; no mutation")
    if not exact:
        return {"result": "ALREADY_COMPLIANT", "changed": False, "scope_hash": event["scope_hash"]}
    rule_id = exact[0].get("SecurityGroupRuleId")
    if not isinstance(rule_id, str) or not re.fullmatch("sgr-[a-f0-9]+", rule_id):
        raise ValueError("exact rule id unavailable")
    ec2.revoke_security_group_ingress(GroupId=group_id, SecurityGroupRuleIds=[rule_id])
    return {"result": "SSH_REVOKED", "changed": True, "scope_hash": event["scope_hash"]}


def lambda_handler(event, context):
    custom = getattr(getattr(context, "client_context", None), "custom", {}) or {}
    if custom.get("bedrockAgentCoreToolName", "").rsplit("___", 1)[-1] != "remove_unrestricted_ssh":
        raise ValueError("Gateway tool context required")
    import boto3
    from botocore.config import Config
    manifest = json.loads(Path(__file__).with_name("scope.json").read_text())
    ec2 = boto3.client("ec2", region_name="ap-southeast-1",
                       config=Config(retries={"total_max_attempts": 1}, connect_timeout=5, read_timeout=10))
    return remediate(ec2, manifest, event)
