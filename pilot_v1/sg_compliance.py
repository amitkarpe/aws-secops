"""Bounded Security Group compliance worker plus exact AWS Config reads.

Owns one SG batch journal; reads only the two approved Config rules; binds
loopback only; no generic AWS operation or direct live remediation fallback.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import threading
from urllib.parse import parse_qs, urlsplit

from .bulk import PolicyDenied
from .gateway import call_tool, result_text

PROFILE = "vagent"
REGION = "ap-southeast-1"
ACTION = "remove_unrestricted_ssh"
TARGET = {"unrestricted_ssh": False}
STATES = {"PENDING", "APPROVED", "RUNNING", "COMPLETED", "SKIPPED", "DENIED", "FAILED", "UNKNOWN"}
CONFIG_RULES = {
    "s3-bucket-level-public-access-prohibited": "AWS::S3::Bucket",
    "restricted-ssh": "AWS::EC2::SecurityGroup",
}
CONFIG_STATUSES = {"COMPLIANT", "NON_COMPLIANT", "INSUFFICIENT_DATA", "NOT_APPLICABLE"}
MAX_CONFIG_RESULTS = 250


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def ssh_evidence(value: object) -> dict[str, bool]:
    if not isinstance(value, dict) or set(value) != {"unrestricted_ssh"} or type(value["unrestricted_ssh"]) is not bool:
        raise ValueError("invalid exact SG evidence")
    return {"unrestricted_ssh": value["unrestricted_ssh"]}


def _iso(value: object) -> str:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, (int, float)):
        dt = datetime.fromtimestamp(value, timezone.utc)
    elif isinstance(value, str):
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError("invalid observation time")
    if dt.tzinfo is None:
        raise ValueError("observation time must be timezone-aware")
    return dt.astimezone(timezone.utc).isoformat()


class ConfigComplianceReader:
    """Read exactly the two demo Config rules. Never mutates Config."""

    def __init__(self, client=None):
        if client is None:
            import boto3
            from botocore.config import Config
            client = boto3.Session(profile_name=PROFILE).client(
                "config", region_name=REGION,
                config=Config(connect_timeout=5, read_timeout=15, retries={"total_max_attempts": 2}),
            )
        self.client = client

    def _recorder_ready(self) -> bool:
        value = self.client.describe_configuration_recorder_status()
        return any(x.get("recording") and x.get("lastStatus") == "SUCCESS"
                   for x in value.get("ConfigurationRecordersStatus", []))

    def _results(self, control: str) -> tuple[list[dict[str, object]], bool]:
        if control not in CONFIG_RULES:
            raise ValueError("unsupported Config control")
        rules = self.client.describe_config_rules(ConfigRuleNames=[control]).get("ConfigRules", [])
        if len(rules) != 1 or rules[0].get("ConfigRuleName") != control:
            raise RuntimeError("required Config rule unavailable")
        expected_type = CONFIG_RULES[control]
        resource_type = "S3_BUCKET" if expected_type == "AWS::S3::Bucket" else "SECURITY_GROUP"
        family = "S3_BPA" if resource_type == "S3_BUCKET" else "SG_RESTRICTED_SSH"
        out: list[dict[str, object]] = []
        token = None
        while len(out) < MAX_CONFIG_RESULTS:
            kwargs: dict[str, object] = {"ConfigRuleName": control, "Limit": min(100, MAX_CONFIG_RESULTS - len(out))}
            if token:
                kwargs["NextToken"] = token
            response = self.client.get_compliance_details_by_config_rule(**kwargs)
            raw = response.get("EvaluationResults", [])
            if not isinstance(raw, list) or len(raw) > int(kwargs["Limit"]):
                raise RuntimeError("Config result exceeds bounded contract")
            for item in raw:
                status = item.get("ComplianceType")
                qualifier = item.get("EvaluationResultIdentifier", {}).get("EvaluationResultQualifier", {})
                if (status not in CONFIG_STATUSES or qualifier.get("ConfigRuleName") != control
                        or qualifier.get("ResourceType") != expected_type):
                    raise RuntimeError("unexpected Config evaluation")
                resource_id = qualifier.get("ResourceId")
                if not isinstance(resource_id, str) or not 1 <= len(resource_id) <= 256:
                    raise RuntimeError("invalid Config resource identity")
                out.append({
                    "finding_id": digest({"source": "AWS Config", "control": control,
                                          "resource_type": resource_type, "resource_id": resource_id}),
                    "source": "AWS Config", "control": control, "resource_type": resource_type,
                    "resource_id": resource_id, "status": status, "severity": "INFO",
                    "remediation_family": family,
                    "remediation_scope": "Config evidence alone cannot authorize execution; exact current demo batch required.",
                    "observed_at": _iso(item.get("ResultRecordedTime")),
                })
            token = response.get("NextToken")
            if not token:
                break
        return out, bool(token)

    def summary(self) -> dict[str, object]:
        if not self._recorder_ready():
            raise RuntimeError("AWS Config recorder is not active and successful")
        controls = []
        for control, expected_type in CONFIG_RULES.items():
            rows, partial = self._results(control)
            counts = dict(Counter(row["status"] for row in rows))
            controls.append({
                "control": control,
                "resource_type": "S3_BUCKET" if expected_type == "AWS::S3::Bucket" else "SECURITY_GROUP",
                "counts": counts, "total_observed": len(rows), "partial": partial,
                "latest_observed_at": max((str(row["observed_at"]) for row in rows), default=None),
            })
        return {
            "version": 1, "source": "AWS Config", "profile": PROFILE, "region": REGION,
            "controls": controls,
            "message": "Config is asynchronous evidence; direct provider readback remains remediation truth.",
        }

    def list_findings(self, control: str, status: str = "NON_COMPLIANT", limit: int = 20,
                      offset: int = 0) -> dict[str, object]:
        if (status not in CONFIG_STATUSES or type(limit) is not int or type(offset) is not int
                or not 1 <= limit <= 50 or not 0 <= offset <= MAX_CONFIG_RESULTS):
            raise ValueError("invalid Config query")
        rows, partial = self._results(control)
        selected = [row for row in rows if row["status"] == status]
        return {"version": 1, "source": "AWS Config", "control": control, "status": status,
                "total": len(selected), "offset": offset, "partial": partial,
                "items": selected[offset:offset + limit]}


class SGProvider:
    """Manifest-bound SG provider. Live writes require GovernedSGProvider."""

    concurrency = 3

    def __init__(self, manifest: Path | str):
        self.manifest = json.loads(Path(manifest).read_text())
        m = self.manifest
        if (m.get("version") != 1 or m.get("profile") != PROFILE or m.get("region") != REGION
                or not re.fullmatch(r"\d{12}", m.get("account", ""))
                or not re.fullmatch(r"[a-f0-9]{16}", m.get("run", ""))
                or not re.fullmatch(r"vpc-[a-f0-9]+", m.get("vpc_id", ""))
                or not 1 <= len(m.get("security_groups", [])) <= 50):
            raise ValueError("invalid SG manifest")
        groups = m["security_groups"]
        if any(set(g) != {"group_id", "name"} for g in groups):
            raise ValueError("invalid SG manifest entry")
        if len({g["group_id"] for g in groups}) != len(groups):
            raise ValueError("duplicate SG manifest entry")
        for group in groups:
            if not re.fullmatch(r"sg-[a-f0-9]+", group["group_id"]):
                raise ValueError("invalid SG id")
            if not re.fullmatch(r"aws-secops-ssh-" + m["run"] + r"-\d{3}", group["name"]):
                raise ValueError("invalid SG name")
        self.entries = {g["group_id"]: g for g in groups}
        self.resources = list(self.entries)
        self.context = {"mode": "LIVE", "profile": PROFILE, "region": REGION, "family": "SECURITY_GROUP",
                        "identity_hash": digest(m["account"]), "manifest_hash": digest(m)}
        self.metrics = {"api_calls": 0, "api_errors": 0, "gateway_calls": 0,
                        "policy_denied": 0, "target_success": 0}
        import boto3
        from botocore.config import Config
        session = boto3.Session(profile_name=PROFILE)
        cfg = Config(connect_timeout=5, read_timeout=15, retries={"total_max_attempts": 2})
        self.ec2 = session.client("ec2", region_name=REGION, config=cfg)
        self.sts = session.client("sts", region_name=REGION, config=cfg)
        self.verify_identity()

    def _call(self, client, method: str, **kwargs):
        self.metrics["api_calls"] += 1
        try:
            return getattr(client, method)(**kwargs)
        except Exception as exc:
            self.metrics["api_errors"] += 1
            code = getattr(exc, "response", {}).get("Error", {}).get("Code", "ProviderError")
            raise RuntimeError(f"provider read failed: {method}; {code}") from None

    def verify_identity(self) -> None:
        if self._call(self.sts, "get_caller_identity").get("Account") != self.manifest["account"]:
            raise PermissionError("wrong live identity")

    def _rules(self, resource: str) -> list[dict[str, object]]:
        value = self._call(self.ec2, "describe_security_group_rules",
                           Filters=[{"Name": "group-id", "Values": [resource]}])
        if value.get("NextToken"):
            raise PermissionError("unexpected SG rule pagination")
        return [x for x in value.get("SecurityGroupRules", []) if not x.get("IsEgress")]

    def guard(self, resource: str) -> None:
        if resource not in self.entries:
            raise PermissionError("outside fixed SG manifest")
        self.verify_identity()
        groups = self._call(self.ec2, "describe_security_groups", GroupIds=[resource]).get("SecurityGroups", [])
        if len(groups) != 1:
            raise PermissionError("SG unavailable")
        group = groups[0]
        expected = self.entries[resource]
        if group.get("VpcId") != self.manifest["vpc_id"] or group.get("GroupName") != expected["name"]:
            raise PermissionError("SG identity differs")
        tags = {x.get("Key"): x.get("Value") for x in group.get("Tags", [])}
        required = {"project": "aws-secops", "owner": "amit", "phase": "bulk-ssh", "run": self.manifest["run"]}
        if any(tags.get(k) != v for k, v in required.items()):
            raise PermissionError("SG ownership tags differ")
        attached = self._call(self.ec2, "describe_network_interfaces",
                              Filters=[{"Name": "group-id", "Values": [resource]}], MaxResults=100)
        if attached.get("NetworkInterfaces") or attached.get("NextToken"):
            raise PermissionError("demo SG is attached; no mutation allowed")

    def read(self, resource: str) -> dict[str, bool]:
        self.guard(resource)
        rules = self._rules(resource)
        exact = [x for x in rules if x.get("IpProtocol") == "tcp" and x.get("FromPort") == 22
                 and x.get("ToPort") == 22 and x.get("CidrIpv4") == "0.0.0.0/0" and not x.get("CidrIpv6")]
        if len(exact) > 1 or any(x not in exact for x in rules):
            raise PermissionError("unexpected ingress on demo SG")
        return {"unrestricted_ssh": bool(exact)}

    def apply(self, resource: str, before: dict[str, bool]):
        raise PermissionError("live SG remediation requires Gateway Policy")


class GovernedSGProvider(SGProvider):
    def __init__(self, manifest: Path | str, deployment: Path | str):
        super().__init__(manifest)
        self.deployment = json.loads(Path(deployment).read_text())
        d = self.deployment
        if d.get("scope_hash") != digest(self.manifest) or d.get("account") != self.manifest["account"]:
            raise ValueError("SG deployment/manifest mismatch")
        self.context["governance_hash"] = digest(d)
        self.batch_id: str | None = None

    def _control(self, operation: str, **kwargs):
        cmd = ["aws", "--profile", PROFILE, "--region", REGION, "--cli-connect-timeout", "5",
               "--cli-read-timeout", "20", "bedrock-agentcore-control", operation]
        for key, value in kwargs.items():
            cmd += ["--" + key.replace("_", "-"), json.dumps(value) if isinstance(value, (dict, list)) else str(value)]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=35,
                                    env={**os.environ, "AWS_MAX_ATTEMPTS": "1", "AWS_PAGER": ""})
        except subprocess.TimeoutExpired:
            raise RuntimeError("AgentCore control-plane read timeout") from None
        if result.returncode:
            raise RuntimeError("AgentCore control-plane read failed")
        value = json.loads(result.stdout or "{}")
        if not isinstance(value, dict):
            raise RuntimeError("AgentCore control-plane returned invalid data")
        return value

    def authorize(self, batch_id: str) -> None:
        self.verify_identity()
        d = self.deployment
        gateway = self._control("get-gateway", gateway_identifier=d["gatewayId"])
        enforced = {"arn": d["policyEngineArn"], "mode": "ENFORCE"}
        if (gateway.get("status") != "READY" or gateway.get("authorizerType") != "AWS_IAM"
                or gateway.get("gatewayUrl") != d["gatewayUrl"]
                or gateway.get("policyEngineConfiguration") != enforced):
            raise PermissionError("SG Gateway enforcement prerequisites differ")
        policy = self._control("get-policy", policy_engine_id=d["policyEngineId"], policy_id=d["policyId"])
        if (policy.get("status") != "ACTIVE" or policy.get("definition") != d["definition"]
                or policy.get("enforcementMode", "ACTIVE") != "ACTIVE"):
            raise PermissionError("SG Policy prerequisites differ")
        policies = self._control("list-policies", policy_engine_id=d["policyEngineId"])
        if policies.get("nextToken") or [x.get("policyId") for x in policies.get("policies", [])] != [d["policyId"]]:
            raise PermissionError("unexpected additional SG Policy scope")
        self.batch_id = batch_id

    def invoke(self, resource: str, environment: str = "dev"):
        if not self.batch_id or resource not in self.resources:
            raise PermissionError("no exact approved SG execution context")
        d = self.deployment
        self.metrics["gateway_calls"] += 1
        response = call_tool(d["gatewayUrl"], REGION, PROFILE, d["toolName"], {
            "scope_hash": d["scope_hash"], "resource_index": self.resources.index(resource),
            "batch_id": self.batch_id, "environment": environment,
        })
        error = response.get("error", {})
        if error.get("code") == -32002 and "Tool Execution Denied" in error.get("message", ""):
            self.metrics["policy_denied"] += 1
            raise PolicyDenied("independent Gateway Policy DENY")
        if error or response.get("result", {}).get("isError"):
            raise RuntimeError("SG Gateway/target error")
        value = json.loads(result_text(response))
        if value.get("scope_hash") != d["scope_hash"] or value.get("result") not in {"SSH_REVOKED", "ALREADY_COMPLIANT"}:
            raise RuntimeError("unexpected SG target result")
        self.metrics["target_success"] += 1
        return {"gateway_decision": "ALLOW", "target_result": value["result"], "target_calls": 1}

    def apply(self, resource: str, before: dict[str, bool]):
        if before != {"unrestricted_ssh": True}:
            raise PermissionError("unexpected approved SG precondition")
        return self.invoke(resource)


class SGBatchStore:
    """One durable SG batch with exact immutable approval and restart safety."""

    def __init__(self, path: Path | str, provider: SGProvider):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.provider = provider
        self.lock = threading.RLock()
        self.worker: threading.Thread | None = None
        self.lease = open(str(self.path) + ".lock", "a")
        try:
            fcntl.flock(self.lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.lease.close()
            raise RuntimeError("SG batch store already has a writer") from None
        self.data = None
        if self.path.exists():
            try:
                raw = self.path.read_bytes()
                if len(raw) > 512_000:
                    raise ValueError("oversize SG store")
                self.data = json.loads(raw)
                self.validate()
                changed = False
                for item in self.data["items"]:
                    if item["state"] == "RUNNING":
                        item.update(state="UNKNOWN", changed=None, message="Interrupted; provider reconciliation required")
                        changed = True
                if changed:
                    self.save()
            except Exception:
                self.close()
                raise RuntimeError("SG batch store corrupt or unreadable; not overwritten") from None

    def close(self) -> None:
        if self.worker and self.worker.is_alive():
            self.worker.join()
        self.lease.close()

    def validate(self) -> None:
        d = self.data
        manifest = d["manifest"]
        if manifest["action"] != ACTION or manifest["target"] != TARGET or manifest["context"] != self.provider.context:
            raise ValueError("SG provider/action mismatch")
        if (type(manifest.get("version")) is not int or not 1 <= manifest["version"] <= 20
                or d["id"] != digest(manifest) or not 1 <= len(manifest["resources"]) <= 50
                or len(d["items"]) != len(manifest["resources"])):
            raise ValueError("SG manifest integrity")
        if d["decision"] not in {"PENDING", "APPROVE"}:
            raise ValueError("invalid SG decision")
        names = set()
        for resource, item in zip(manifest["resources"], d["items"]):
            rid = resource["resource"]
            ssh_evidence(resource["before"])
            if not re.fullmatch(r"sg-[a-f0-9]+", rid) or rid in names:
                raise ValueError("SG resource integrity")
            names.add(rid)
            if item["id"] != digest(resource) or item["resource"] != rid or item["state"] not in STATES:
                raise ValueError("SG item integrity")
        if set(names) != set(self.provider.resources):
            raise ValueError("configured SG manifest changed")

    def save(self) -> None:
        self.validate()
        self.data["usage"] = dict(self.provider.metrics, scope="provider process cumulative; no billing inference")
        raw = json.dumps(self.data).encode()
        if len(raw) > 512_000:
            raise ValueError("SG store size limit")
        temp = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.path.parent, delete=False) as stream:
                temp = stream.name
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            os.replace(temp, self.path)
            directory = os.open(self.path.parent, os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if temp and os.path.exists(temp):
                os.unlink(temp)

    def preview(self, renew: bool = False) -> dict[str, object]:
        with self.lock:
            if self.data and not renew:
                return self.summary()
            if self.data and any(i["state"] in {"PENDING", "APPROVED", "RUNNING", "UNKNOWN"} for i in self.data["items"]):
                raise ValueError("resolve current SG batch before new preview")
            revision = 1
            if self.data:
                self.validate()
                revision = self.data["manifest"]["version"] + 1
                if revision > 20:
                    raise ValueError("twenty retained SG previews; archive review required")
                archive = self.path.with_name(self.path.name + "." + self.data["id"])
                if not archive.exists():
                    with archive.open("xb") as out:
                        out.write(self.path.read_bytes()); out.flush(); os.fsync(out.fileno())
            evidence = [{"resource": rid, "before": ssh_evidence(self.provider.read(rid))}
                        for rid in sorted(self.provider.resources)]
            manifest = {"version": revision, "context": deepcopy(self.provider.context), "action": ACTION,
                        "target": dict(TARGET), "resources": evidence}
            self.data = {
                "id": digest(manifest), "manifest": manifest, "decision": "PENDING",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "items": [{"id": digest(r), "resource": r["resource"], "state": "PENDING",
                           "after": None, "changed": False, "message": "Awaiting native human approval"}
                          for r in evidence],
            }
            self.save()
            return self.summary()

    def require(self, batch_id: str) -> None:
        if not self.data or batch_id != self.data["id"]:
            raise ValueError("unknown or stale SG batch")
        self.validate()

    def start(self, batch_id: str, approval_hash: str) -> dict[str, object]:
        with self.lock:
            self.require(batch_id)
            if approval_hash != self.data["id"] or self.data["decision"] != "PENDING":
                raise ValueError("stale/consumed SG approval")
            if self.worker and self.worker.is_alive():
                raise ValueError("SG execution already active")
            if any(i["state"] in {"RUNNING", "UNKNOWN"} for i in self.data["items"]):
                raise ValueError("SG reconciliation required")
            if hasattr(self.provider, "authorize"):
                self.provider.authorize(batch_id)
            self.data["decision"] = "APPROVE"
            for item in self.data["items"]:
                item.update(state="APPROVED", message="Native human approval consumed for exact SG batch")
            self.save()
            self.worker = threading.Thread(target=self._run, args=(batch_id,), daemon=False)
            self.worker.start()
            return self.summary()

    def step(self, batch_id: str) -> dict[str, object]:
        with self.lock:
            self.require(batch_id)
            if self.data["decision"] != "APPROVE" or any(i["state"] == "UNKNOWN" for i in self.data["items"]):
                raise ValueError("SG approval/reconciliation required")
            item = next((i for i in self.data["items"] if i["state"] == "APPROVED"), None)
            if item is None:
                return self.summary()
            approved = next(r for r in self.data["manifest"]["resources"] if r["resource"] == item["resource"])
            item.update(state="RUNNING", changed=None, message="Claimed durably; outcome not yet known")
            self.save()
        dispatched = False
        try:
            current = ssh_evidence(self.provider.read(item["resource"]))
            if current == TARGET:
                update = {"state": "SKIPPED", "after": current, "changed": False,
                          "message": "Provider already compliant; no dispatch"}
            elif current != approved["before"]:
                update = {"state": "DENIED", "after": current, "changed": False,
                          "message": "SG drift; stale approval blocked"}
            else:
                dispatched = True
                audit = self.provider.apply(item["resource"], current)
                after = ssh_evidence(self.provider.read(item["resource"]))
                update = {"state": "COMPLETED" if after == TARGET else "FAILED", "after": after,
                          "changed": after != current,
                          "message": "Provider verified restricted SSH" if after == TARGET else "SG postcondition not met"}
                if isinstance(audit, dict):
                    update["audit"] = audit
        except PolicyDenied:
            update = {"state": "DENIED", "changed": False, "message": "Gateway Policy DENY; target not dispatched",
                      "audit": {"gateway_decision": "DENY", "target_calls": 0}}
        except Exception:
            update = {"state": "UNKNOWN" if dispatched else "FAILED", "changed": None if dispatched else False,
                      "message": "Dispatch/readback uncertain; reconcile before retry" if dispatched
                                 else "Pre-read failed; no dispatch"}
        with self.lock:
            item.update(update)
            self.save()
            return self.summary()

    def _run(self, batch_id: str) -> None:
        try:
            with ThreadPoolExecutor(max_workers=self.provider.concurrency) as pool:
                while True:
                    with self.lock:
                        if any(i["state"] == "UNKNOWN" for i in self.data["items"]):
                            return
                        count = sum(i["state"] == "APPROVED" for i in self.data["items"])
                    if not count:
                        return
                    futures = [pool.submit(self.step, batch_id)
                               for _ in range(min(count, self.provider.concurrency))]
                    for future in futures:
                        future.result()
        except Exception:
            return

    def reconcile(self, batch_id: str) -> dict[str, object]:
        with self.lock:
            self.require(batch_id)
            for item in self.data["items"]:
                if item["state"] != "UNKNOWN":
                    continue
                try:
                    after = ssh_evidence(self.provider.read(item["resource"]))
                    item.update(state="COMPLETED" if after == TARGET else "FAILED", after=after, changed=None,
                                message="Read-only reconciliation; no blind retry")
                except Exception:
                    item["message"] = "Reconciliation unavailable; remains UNKNOWN"
                self.save()
            return self.summary()

    def summary(self) -> dict[str, object]:
        with self.lock:
            if not self.data:
                return {"version": 1, "batch": None}
            self.validate()
            counts = dict(Counter(i["state"] for i in self.data["items"]))
            return {
                "version": 1, "family": "SECURITY_GROUP", "batch_id": self.data["id"],
                "approval_hash": self.data["id"], "action": ACTION, "target": dict(TARGET),
                "context": deepcopy(self.provider.context), "total": len(self.data["items"]),
                "decision": self.data["decision"], "counts": counts,
                "verified": counts.get("COMPLETED", 0) + counts.get("SKIPPED", 0),
                "observed_at": self.data["created_at"],
                "execution_active": bool(self.worker and self.worker.is_alive()),
                "usage": deepcopy(self.data.get("usage", {})),
                "message": "Unattached demo SGs only; COMPLETED/SKIPPED requires direct EC2 readback.",
            }

    def page(self, batch_id: str, offset: int = 0, limit: int = 20,
             state: str | None = None) -> dict[str, object]:
        with self.lock:
            self.require(batch_id)
            if (type(offset) is not int or type(limit) is not int or not 0 <= offset <= 50
                    or not 1 <= limit <= 50 or state not in STATES | {None}):
                raise ValueError("invalid SG pagination")
            rows = [i for i in self.data["items"] if state is None or i["state"] == state]
            before = {r["resource"]: r["before"] for r in self.data["manifest"]["resources"]}
            selected = deepcopy(rows[offset:offset + limit])
            for item in selected:
                item["before"] = deepcopy(before[item["resource"]])
            return {"version": 1, "summary": self.summary(), "total": len(rows),
                    "offset": offset, "items": selected}


class Service:
    def __init__(self, store: SGBatchStore, config: ConfigComplianceReader):
        self.store = store
        self.config = config

    def query(self, operation: str, args: dict[str, object]):
        if operation == "list_sg_batches" and not args:
            return {"version": 1, "items": [self.store.summary()] if self.store.data else []}
        if operation == "get_sg_batch" and "batch_id" in args and not set(args) - {"batch_id", "offset", "limit", "state"}:
            return self.store.page(**args)
        if operation == "get_config_summary" and not args:
            return self.config.summary()
        if operation == "list_config_findings" and "control" in args and not set(args) - {"control", "status", "offset", "limit"}:
            return self.config.list_findings(**args)
        raise ValueError("unsupported compliance query")


class Handler(BaseHTTPRequestHandler):
    service: Service

    def log_message(self, format: str, *args: object) -> None:
        return

    def _host_ok(self) -> bool:
        return self.headers.get_all("Host") in ([f"localhost:{self.server.server_port}"],
                                                 [f"127.0.0.1:{self.server.server_port}"])

    def _origin_ok(self) -> bool:
        host = urlsplit(f"//{self.headers.get('Host', '')}")
        origin = urlsplit(self.headers.get("Origin", ""))
        return (origin.scheme == "http" and origin.hostname == host.hostname and origin.port == host.port
                and not origin.path and not origin.query and not origin.fragment)

    def _json(self, status: int, value: object) -> None:
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if not self._host_ok():
            self._json(403, {"error": "unexpected local Host"})
            return
        parsed = urlsplit(self.path)
        if not parsed.path.startswith("/api/v1/"):
            self._json(404, {"error": "not found"})
            return
        try:
            query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True, max_num_fields=5)
            if any(len(v) != 1 for v in query.values()):
                raise ValueError("duplicate argument")
            args: dict[str, object] = {k: v[0] for k, v in query.items()}
            for key in ("offset", "limit"):
                if key in args:
                    args[key] = int(args[key])
            self._json(200, self.service.query(parsed.path.removeprefix("/api/v1/"), args))
        except ValueError:
            self._json(400, {"error": "invalid compliance query"})
        except Exception:
            self._json(503, {"error": "compliance backend unavailable; no action performed"})

    def do_POST(self) -> None:
        if not self._host_ok() or not self._origin_ok():
            self._json(403, {"error": "same loopback origin required"})
            return
        if self.headers.get_content_type() != "application/json":
            self._json(415, {"error": "application/json required"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 <= length <= 4096:
                raise ValueError("payload too large")
            data = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(data, dict):
                raise ValueError("object required")
            if self.path == "/api/sg/preview" and not data:
                result = self.service.store.preview()
            elif self.path == "/api/sg/new-preview" and not data:
                result = self.service.store.preview(renew=True)
            elif self.path == "/api/sg/start" and set(data) == {"batch_id", "approval_hash"}:
                result = self.service.store.start(**data)
            elif self.path == "/api/sg/reconcile" and set(data) == {"batch_id"}:
                result = self.service.store.reconcile(**data)
            else:
                raise ValueError("unsupported SG action")
            self._json(200, result)
        except (ValueError, RuntimeError):
            self._json(400, {"error": "request rejected; inspect durable SG state before retry"})
        except Exception:
            self._json(503, {"error": "SG operation unavailable; no automatic retry"})


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--gateway-state", type=Path, required=True)
    p.add_argument("--state", type=Path, required=True)
    p.add_argument("--port", type=int, default=4455)
    args = p.parse_args()
    if not 1024 <= args.port <= 65535:
        p.error("invalid loopback port")
    provider = GovernedSGProvider(args.manifest, args.gateway_state)
    store = SGBatchStore(args.state, provider)
    Handler.service = Service(store, ConfigComplianceReader())
    try:
        with HTTPServer(("127.0.0.1", args.port), Handler) as server:
            print(f"SG_COMPLIANCE=http://localhost:{args.port} COUNT={len(provider.resources)}", flush=True)
            server.serve_forever()
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
