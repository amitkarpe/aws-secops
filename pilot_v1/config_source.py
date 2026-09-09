"""Bounded read-only AWS Config intake for the personal Singapore lab."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from typing import Any

from .findings import MAX_FINDINGS, validate_finding

SOURCE = "AWS Config"
MAX_RULES = 10


def _read(operation: str, arguments: list[str]) -> dict[str, Any]:
    command = [
        "aws", "configservice", operation, "--profile", "amit",
        "--region", "ap-southeast-1", "--output", "json", "--no-paginate",
        "--cli-connect-timeout", "10", "--cli-read-timeout", "30", *arguments,
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=45)
        if result.returncode:
            raise RuntimeError("AWS Config read failed; check local credentials/access")
        payload = json.loads(result.stdout)
        if not isinstance(payload, dict):
            raise ValueError("invalid response")
        return payload
    except (subprocess.TimeoutExpired, ValueError) as exc:
        raise RuntimeError("AWS Config returned an unavailable or invalid response") from exc


def normalize_evaluation(value: dict[str, Any]) -> dict[str, str]:
    qualifier = value["EvaluationResultIdentifier"]["EvaluationResultQualifier"]
    resource_id = qualifier["ResourceId"]
    # Some Config identifiers are ARNs longer than the common text limit.
    if len(resource_id) > 128:
        resource_id = "resource-sha256:" + hashlib.sha256(resource_id.encode()).hexdigest()
    observed = value["ResultRecordedTime"]
    if isinstance(observed, (int, float)):
        observed = datetime.fromtimestamp(observed, timezone.utc).isoformat()
    observed = datetime.fromisoformat(observed.replace("Z", "+00:00"))
    if observed.tzinfo is None:
        raise ValueError("Config evaluation time must include a timezone")
    annotation = " ".join(str(value.get("Annotation", "")).split())[:350]
    return validate_finding({
        "source": SOURCE,
        "resource_type": {
            "AWS::EC2::SecurityGroup": "SECURITY_GROUP",
            "AWS::S3::Bucket": "S3_BUCKET",
            "AWS::EC2::Instance": "EC2_INSTANCE",
        }.get(qualifier["ResourceType"], qualifier["ResourceType"]),
        "resource_id": resource_id,
        "resource_name": resource_id,
        "environment": "demo",
        "control": qualifier["ConfigRuleName"],
        "severity": "INFO",  # Config evaluation results do not assign severity.
        "status": value["ComplianceType"],
        "evidence": "AWS Config recorded this evaluation. " + annotation,
        "recommendation": "Review the Config rule and resource configuration; prepare a change plan for separate review.",
        "observed_at": observed.astimezone(timezone.utc).isoformat(),
    })


def fetch_config_findings() -> dict[str, Any]:
    recorders = _read("describe-configuration-recorder-status", [])
    if not any(item.get("recording") and item.get("lastStatus") == "SUCCESS"
               for item in recorders.get("ConfigurationRecordersStatus", [])):
        raise RuntimeError("AWS Config recorder is not active and successful")
    summary = _read("describe-compliance-by-config-rule", ["--compliance-types", "NON_COMPLIANT"])
    rules = summary.get("ComplianceByConfigRules")
    if not isinstance(rules, list):
        raise RuntimeError("AWS Config returned no rule summary")
    partial = bool(summary.get("NextToken")) or len(rules) > MAX_RULES
    findings = []
    for rule in rules[:MAX_RULES]:
        remaining = MAX_FINDINGS - len(findings)
        if not remaining:
            partial = True
            break
        detail = _read("get-compliance-details-by-config-rule", [
            "--config-rule-name", rule["ConfigRuleName"],
            "--compliance-types", "NON_COMPLIANT", "--limit", str(remaining),
        ])
        evaluations = detail.get("EvaluationResults")
        if not isinstance(evaluations, list) or len(evaluations) > remaining:
            raise RuntimeError("AWS Config evaluation result exceeds the bounded contract")
        partial = partial or bool(detail.get("NextToken"))
        for evaluation in evaluations:
            if evaluation.get("ComplianceType") != "NON_COMPLIANT":
                raise RuntimeError("AWS Config returned an unexpected compliance status")
            findings.append(normalize_evaluation(evaluation))
    return {
        "findings": findings,
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "status": "PARTIAL" if partial else "SUCCESS",
        "scope": "Noncompliant evaluations; up to 10 rules / 100 records; no pagination",
    }
