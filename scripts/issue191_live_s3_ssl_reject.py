#!/usr/bin/env python3
"""Issue #191 fixed personal-LAB S3 TLS read and no-dispatch Reject proof.

This performs AWS read APIs only: Organizations ListAccounts, STS AssumeRole /
GetCallerIdentity, S3 ListBuckets, and S3 GetBucketPolicy. It never invokes a
remediation executor, does not accept bucket or account inputs, and prints only
aliases, counts, digests, frozen batch digests, and Reject/audit results.
"""
from __future__ import annotations

import json
import sys

import boto3

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agents" / "compliance-agent-v1" / "src"))

from compliance_agent_v1.live_s3_ssl import (  # noqa: E402
    ALIASES, AccountBinding, REGION, collect_with_boto3, prepare_reject,
)


def main() -> int:
    source = boto3.Session(profile_name="amit", region_name=REGION)
    accounts = source.client("organizations", region_name=REGION).list_accounts()["Accounts"]
    by_alias = {row.get("Name"): row.get("Id") for row in accounts if row.get("Name") in ALIASES and row.get("Status") == "ACTIVE"}
    if set(by_alias) != set(ALIASES) or any(not isinstance(by_alias[alias], str) for alias in ALIASES):
        raise SystemExit("LAB_ALIAS_GATE_FAILED")
    bindings = tuple(AccountBinding(alias, by_alias[alias]) for alias in ALIASES)
    before = collect_with_boto3(profile="amit", bindings=bindings)
    proof = prepare_reject(before, alias="lab-dev")
    # A fresh provider readback is required even for Reject: neither this
    # runner nor the local decision path has an AWS write capability.
    after = collect_with_boto3(profile="amit", bindings=bindings)
    unchanged = before["evidence_digest"] == after["evidence_digest"]
    if not unchanged:
        raise SystemExit("POST_REJECT_READBACK_CHANGED")
    value = {
        "version": 1,
        "control": proof["control"],
        "alias": proof["alias"],
        "region": REGION,
        "provider_evidence_digest": before["evidence_digest"],
        "post_reject_evidence_digest": after["evidence_digest"],
        "provider_readback_unchanged": unchanged,
        "batch_id_digest": proof["preview"]["batch_id"],
        "scope_hash_digest": proof["preview"]["scope_hash"],
        "decision": proof["result"]["decision"],
        "remediation_dispatches": proof["remediation_dispatches"],
        "aws_writes": proof["aws_writes"],
        "audit_event_types": proof["audit"]["event_types"],
        "account_states": [{"alias": row["alias"], "identity_verified": row["identity_verified"], "state": row["state"], "provider_evidence_digest": row.get("provider_evidence_digest")} for row in after["accounts"]],
        "read_only": True,
        "automated_approve": False,
    }
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
