#!/usr/bin/env python3
"""Create/read/reset/cleanup exact unattached SG demo fleets (10 or 50 only)."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import secrets
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PROFILE = "vagent"
REGION = "ap-southeast-1"


def save(path: Path, value: dict) -> None:
    temp = path.with_suffix(path.suffix + ".new")
    with temp.open("w") as out:
        json.dump(value, out); out.flush(); os.fsync(out.fileno())
    temp.replace(path)


def clients():
    import boto3
    from botocore.config import Config
    session = boto3.Session(profile_name=PROFILE)
    cfg = Config(connect_timeout=5, read_timeout=15, retries={"total_max_attempts": 2})
    return session.client("sts", region_name=REGION, config=cfg), session.client("ec2", region_name=REGION, config=cfg)


def identity(sts, account: str) -> None:
    if sts.get_caller_identity().get("Account") != account:
        raise PermissionError("vagent identity mismatch")


def exact_ingress(ec2, group_id: str):
    response = ec2.describe_security_group_rules(Filters=[{"Name": "group-id", "Values": [group_id]}])
    if response.get("NextToken"):
        raise RuntimeError("unexpected SG rule pagination")
    return [x for x in response.get("SecurityGroupRules", []) if not x.get("IsEgress")]


def is_exact_ssh(rule: dict) -> bool:
    return (rule.get("IpProtocol") == "tcp" and rule.get("FromPort") == 22 and rule.get("ToPort") == 22
            and rule.get("CidrIpv4") == "0.0.0.0/0" and not rule.get("CidrIpv6"))


def guard(ec2, manifest: dict, entry: dict) -> bool:
    group_id = entry["group_id"]
    groups = ec2.describe_security_groups(GroupIds=[group_id]).get("SecurityGroups", [])
    if len(groups) != 1:
        raise RuntimeError("demo SG unavailable")
    group = groups[0]
    if group.get("VpcId") != manifest["vpc_id"] or group.get("GroupName") != entry["name"]:
        raise RuntimeError("demo SG identity changed")
    tags = {x.get("Key"): x.get("Value") for x in group.get("Tags", [])}
    required = {"project": "aws-secops", "owner": "amit", "phase": "bulk-ssh", "run": manifest["run"]}
    if any(tags.get(k) != v for k, v in required.items()):
        raise RuntimeError("demo SG ownership tags changed")
    attached = ec2.describe_network_interfaces(Filters=[{"Name": "group-id", "Values": [group_id]}], MaxResults=100)
    if attached.get("NetworkInterfaces") or attached.get("NextToken"):
        raise RuntimeError("demo SG attached; stop")
    ingress = exact_ingress(ec2, group_id)
    exact = [x for x in ingress if is_exact_ssh(x)]
    if len(exact) > 1 or any(x not in exact for x in ingress):
        raise RuntimeError("unexpected ingress on demo SG")
    return bool(exact)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["create", "read", "reset", "cleanup"])
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--account-file", type=Path, help="private STS JSON; create only")
    p.add_argument("--vpc-id", help="existing personal-lab VPC; create only")
    p.add_argument("--count", type=int, choices=[10, 50], default=10)
    p.add_argument("--ttl", help="review date DD-MM-YY; create only")
    args = p.parse_args(); os.umask(0o077)
    sts, ec2 = clients()

    if args.action == "create":
        if args.manifest.exists() or not args.account_file or not args.vpc_id or not args.ttl:
            p.error("create requires new manifest, --account-file, --vpc-id and --ttl")
        if not re.fullmatch(r"vpc-[a-f0-9]+", args.vpc_id):
            p.error("invalid VPC id")
        account = json.loads(args.account_file.read_text()).get("Account")
        if not isinstance(account, str) or not re.fullmatch(r"\d{12}", account):
            p.error("invalid private account evidence")
        identity(sts, account)
        vpcs = ec2.describe_vpcs(VpcIds=[args.vpc_id]).get("Vpcs", [])
        if len(vpcs) != 1 or vpcs[0].get("State") != "available":
            p.error("existing VPC unavailable")
        if datetime.strptime(args.ttl, "%d-%m-%y").date() < datetime.now(timezone.utc).date():
            p.error("TTL expired")
        run = secrets.token_hex(8)
        manifest = {"version": 1, "profile": PROFILE, "region": REGION, "account": account,
                    "run": run, "vpc_id": args.vpc_id, "security_groups": []}
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        save(args.manifest, manifest)
        try:
            for i in range(args.count):
                name = f"aws-secops-ssh-{run}-{i:03d}"
                tags = {
                    "Name": name, "owner": "amit", "project": "aws-secops", "phase": "bulk-ssh", "run": run,
                    "environment": "dev", "purpose": "unattached restricted-ssh compliance demo",
                    "TTL": args.ttl, "cleanup": "review", "created": datetime.now(timezone.utc).date().isoformat(),
                }
                created = ec2.create_security_group(
                    GroupName=name, Description="unattached restricted-ssh compliance demo", VpcId=args.vpc_id,
                    TagSpecifications=[{"ResourceType": "security-group",
                                        "Tags": [{"Key": k, "Value": v} for k, v in tags.items()]}],
                )
                entry = {"group_id": created["GroupId"], "name": name}
                manifest["security_groups"].append(entry); save(args.manifest, manifest)
                ec2.authorize_security_group_ingress(GroupId=entry["group_id"], IpPermissions=[{
                    "IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "aws-secops restricted-ssh demo"}],
                }])
                if not guard(ec2, manifest, entry):
                    raise RuntimeError("creation readback failed")
        except Exception:
            print("CREATE_PARTIAL_MANIFEST_SAVED=" + str(args.manifest), file=sys.stderr)
            raise
        print(f"CREATED={len(manifest['security_groups'])} UNATTACHED=YES")
        return 0

    manifest = json.loads(args.manifest.read_text())
    if (manifest.get("profile") != PROFILE or manifest.get("region") != REGION
            or not 1 <= len(manifest.get("security_groups", [])) <= 50):
        p.error("invalid manifest")
    identity(sts, manifest["account"])
    if args.action == "read":
        noncompliant = sum(int(guard(ec2, manifest, entry)) for entry in manifest["security_groups"])
        print(f"TOTAL={len(manifest['security_groups'])} NON_COMPLIANT={noncompliant} COMPLIANT={len(manifest['security_groups'])-noncompliant}")
        return 0

    if args.action == "reset":
        changed = 0
        for entry in manifest["security_groups"]:
            if not guard(ec2, manifest, entry):
                ec2.authorize_security_group_ingress(GroupId=entry["group_id"], IpPermissions=[{
                    "IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "aws-secops restricted-ssh demo"}],
                }])
                if not guard(ec2, manifest, entry):
                    raise RuntimeError("reset readback failed")
                changed += 1
        print(f"RESET_NON_COMPLIANT={len(manifest['security_groups'])} CHANGED={changed}")
        return 0

    for entry in manifest["security_groups"]:
        guard(ec2, manifest, entry)
    for entry in manifest["security_groups"]:
        ec2.delete_security_group(GroupId=entry["group_id"])
    remaining = {x["GroupId"] for x in ec2.describe_security_groups(
        Filters=[{"Name": "vpc-id", "Values": [manifest["vpc_id"]]}]).get("SecurityGroups", [])}
    if remaining.intersection(x["group_id"] for x in manifest["security_groups"]):
        raise RuntimeError("cleanup readback failed")
    print(f"CLEANED={len(manifest['security_groups'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
