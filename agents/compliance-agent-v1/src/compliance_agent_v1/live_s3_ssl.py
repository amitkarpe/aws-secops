"""Fixed, read-only LAB S3 TLS evidence and Reject-only preparation adapter.

The collector has one query family (bucket transport-policy posture), one
registered alias set, and one fixed cross-account role. It never accepts an AWS
operation or resource from a model and has no mutation method.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Callable, Mapping, Protocol

CONTROL = "s3_ssl"
ALIASES = ("lab-dev", "lab-poc", "lab-qa", "lab-sec")
ROLE_NAME = "ChatGPTCrossAccountReadRole"
REGION = "ap-southeast-1"
MAX_BUCKETS_PER_ACCOUNT = 20


class S3ReadClient(Protocol):
    def caller_account(self) -> str: ...
    def list_bucket_names(self) -> list[str]: ...
    def bucket_policy(self, bucket: str) -> Mapping[str, Any]: ...


class _BotoS3ReadClient:
    """Private server-side AWS client; output remains normalized and alias-only."""

    def __init__(self, session: Any):
        self._sts = session.client("sts", region_name=REGION)
        self._s3 = session.client("s3", region_name=REGION)

    def caller_account(self) -> str:
        return str(self._sts.get_caller_identity()["Account"])

    def list_bucket_names(self) -> list[str]:
        paginator = self._s3.get_paginator("list_buckets")
        result: list[str] = []
        for page in paginator.paginate(PaginationConfig={"PageSize": MAX_BUCKETS_PER_ACCOUNT, "MaxItems": MAX_BUCKETS_PER_ACCOUNT}):
            result.extend(str(item["Name"]) for item in page.get("Buckets", [])
                          if isinstance(item, Mapping) and isinstance(item.get("Name"), str))
        return result[:MAX_BUCKETS_PER_ACCOUNT]

    def bucket_policy(self, bucket: str) -> Mapping[str, Any]:
        return json.loads(self._s3.get_bucket_policy(Bucket=bucket)["Policy"])


@dataclass(frozen=True)
class AccountBinding:
    alias: str
    account_id: str


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _resource_ref(bucket: str) -> str:
    return "bucket-ref-" + hashlib.sha256(bucket.encode("utf-8")).hexdigest()[:12]


def _requires_secure_transport(policy: Mapping[str, Any]) -> bool:
    statements = policy.get("Statement", [])
    if isinstance(statements, Mapping):
        statements = [statements]
    if not isinstance(statements, list):
        return False
    for statement in statements:
        if not isinstance(statement, Mapping) or statement.get("Effect") != "Deny":
            continue
        condition = statement.get("Condition", {})
        bool_values = condition.get("Bool", {}) if isinstance(condition, Mapping) else {}
        if isinstance(bool_values, Mapping) and str(bool_values.get("aws:SecureTransport", "")).lower() == "false":
            return True
    return False


class LiveS3SslEvidence:
    """Collect public-safe evidence from verified fixed LAB account bindings."""

    def __init__(self, bindings: tuple[AccountBinding, ...], client_factory: Callable[[AccountBinding], S3ReadClient]):
        if tuple(binding.alias for binding in bindings) != ALIASES:
            raise ValueError("bindings must be the exact registered LAB aliases in order")
        self.bindings = bindings
        self._client_factory = client_factory

    def collect(self) -> dict[str, Any]:
        accounts: list[dict[str, Any]] = []
        for binding in self.bindings:
            client = self._client_factory(binding)
            verified = client.caller_account() == binding.account_id
            if not verified:
                accounts.append({"alias": binding.alias, "identity_verified": False, "state": "UNAVAILABLE", "reason": "ACCOUNT_MISMATCH"})
                continue
            statuses: list[dict[str, str]] = []
            for bucket in sorted(client.list_bucket_names())[:MAX_BUCKETS_PER_ACCOUNT]:
                reference = _resource_ref(bucket)
                try:
                    policy = client.bucket_policy(bucket)
                    status = "COMPLIANT" if _requires_secure_transport(policy) else "NON_COMPLIANT"
                except Exception as exc:
                    # A bucket with no policy is explicitly non-compliant for this
                    # control; all other provider failures remain unavailable.
                    status = "NON_COMPLIANT" if "NoSuchBucketPolicy" in str(exc) else "UNAVAILABLE"
                statuses.append({"resource_ref": reference, "status": status})
            statuses.sort(key=lambda item: (item["resource_ref"], item["status"]))
            payload = {"alias": binding.alias, "statuses": statuses}
            accounts.append({
                "alias": binding.alias,
                "identity_verified": True,
                "region": REGION,
                "state": "AVAILABLE" if statuses else "UNAVAILABLE",
                "resource_count": len(statuses),
                "status_counts": {state: sum(item["status"] == state for item in statuses) for state in ("COMPLIANT", "NON_COMPLIANT", "UNAVAILABLE")},
                "provider_evidence_digest": _digest(payload),
                "statuses": statuses,
            })
        return {"version": 1, "control": CONTROL, "role": ROLE_NAME, "region": REGION,
                "accounts": accounts, "read_only": True, "aws_writes": 0,
                "raw_identifiers_emitted": False,
                "evidence_digest": _digest(accounts)}


class LiveS3FindingStore:
    """Minimal finding-store adapter for one exact live read-derived batch."""

    def __init__(self, evidence: Mapping[str, Any]):
        rows: list[dict[str, str]] = []
        for account in evidence.get("accounts", []):
            for index, status in enumerate(account.get("statuses", []), start=1):
                rows.append({
                    "finding_id": f"f-live-{account['alias']}-{CONTROL}-{index:02d}",
                    "account_alias": account["alias"], "control_key": CONTROL,
                    "resource_id": status["resource_ref"], "config_status": status["status"],
                    "provider_status": status["status"], "exception_status": "NONE",
                    "remediation_status": "NOT_STARTED", "region": REGION,
                })
        self._rows = tuple(rows)
        self._digest = str(evidence["evidence_digest"])

    def evidence_receipt(self) -> dict[str, Any]:
        return {"version": 1, "fixture": "live-s3-ssl-read", "evidence_digest": self._digest, "read_only": True}

    def resolve_finding_id(self, finding_id: str) -> dict[str, str] | None:
        return next((dict(row) for row in self._rows if row["finding_id"] == finding_id), None)


def prepare_reject(evidence: Mapping[str, Any], *, alias: str) -> dict[str, Any]:
    """Prepare one exact live-read finding and apply the local Reject contract.

    This is deliberately not a substitute for the authenticated LibreChat
    native-card journey.  It reuses the same bounded freeze/decision/audit
    implementation to prove that the read adapter cannot dispatch remediation.
    """
    account = next((row for row in evidence["accounts"] if row.get("alias") == alias), None)
    if not account or account.get("state") != "AVAILABLE":
        raise ValueError("selected LAB alias has unavailable s3_ssl evidence")
    finding_ids = [
        f"f-live-{alias}-{CONTROL}-{index:02d}"
        for index, row in enumerate(account.get("statuses", []), start=1)
        if row.get("status") == "NON_COMPLIANT"
    ]
    if not finding_ids:
        raise ValueError("selected LAB alias has no current s3_ssl finding")
    from .exceptions_audit import ExceptionAuditPilot
    pilot = ExceptionAuditPilot(LiveS3FindingStore(evidence), control=CONTROL)
    pilot.add(finding_ids[0])
    preview = pilot.preview_selection()
    result = pilot.decide(preview["batch_id"], preview["scope_hash"], "REJECT")
    return {"control": CONTROL, "alias": alias, "preview": preview, "result": result,
            "audit": pilot.ledger.timeline(preview["batch_id"]), "aws_writes": 0,
            "remediation_dispatches": 0, "read_only": True}


def collect_with_boto3(*, profile: str, bindings: tuple[AccountBinding, ...]) -> dict[str, Any]:
    """Run the fixed personal-LAB read path through existing cross-account roles.

    This function deliberately supports only the personal interactive profile
    or the retained-host profile, with exact organization-derived bindings.
    """
    if profile not in {"amit", "vagent"}:
        raise ValueError("live s3_ssl collector requires an approved personal-LAB profile")
    import boto3

    source = boto3.Session(profile_name=profile, region_name=REGION)
    if not all(isinstance(binding.account_id, str) and len(binding.account_id) == 12 and binding.account_id.isdigit() for binding in bindings):
        raise ValueError("invalid exact LAB account bindings")

    def client_factory(binding: AccountBinding) -> S3ReadClient:
        credentials = source.client("sts", region_name=REGION).assume_role(
            RoleArn=f"arn:aws:iam::{binding.account_id}:role/{ROLE_NAME}",
            RoleSessionName="issue191-s3-ssl-read",
        )["Credentials"]
        session = boto3.Session(
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
            region_name=REGION,
        )
        return _BotoS3ReadClient(session)

    return LiveS3SslEvidence(bindings, client_factory).collect()


__all__ = ["AccountBinding", "ALIASES", "CONTROL", "LiveS3FindingStore", "LiveS3SslEvidence", "REGION", "ROLE_NAME", "collect_with_boto3", "prepare_reject"]
