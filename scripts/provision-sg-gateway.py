#!/usr/bin/env python3
"""Explicit same-account Gateway/Policy/Lambda deployment for exact SG remediation.

Private resumable state. No SG creation/reset/write here. Ambiguous create/update
failures stop; resources are retained for review rather than silently retried.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pilot_v1.sg_compliance import SGProvider, digest, REGION

ERROR_FILE = None


def aws(service, operation, **arguments):
    cmd = ["aws", "--profile", "vagent", "--region", REGION, "--cli-connect-timeout", "5", "--cli-read-timeout", "30", service, operation]
    for key, value in arguments.items():
        cmd += ["--" + key.replace("_", "-"), json.dumps(value) if isinstance(value, (list, dict)) else str(value)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                            env={**os.environ, "AWS_MAX_ATTEMPTS": "1", "AWS_PAGER": ""})
    if result.returncode:
        if ERROR_FILE:
            ERROR_FILE.write_text(result.stderr)
        code = re.search(r"\((\w+)\)", result.stderr)
        raise RuntimeError(f"{service}:{operation}: {code.group(1) if code else 'FAILED'}; inspect private provider state before retry")
    return json.loads(result.stdout or "{}")


def wait(read, field, ready, expected=None):
    for _ in range(30):
        value = read()
        if value.get(field) == ready and all(value.get(k) == v for k, v in (expected or {}).items()):
            return value
        if value.get(field) in {"FAILED", "CREATE_FAILED", "UPDATE_FAILED"}:
            raise RuntimeError("resource failed; retained for review")
        time.sleep(2)
    raise RuntimeError("bounded readiness timeout; retained for review")


def main() -> int:
    global ERROR_FILE
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--state", type=Path, required=True)
    p.add_argument("--ttl", required=True)
    p.add_argument("--create", action="store_true")
    p.add_argument("--replace-scope", action="store_true")
    args = p.parse_args(); os.umask(0o077)
    ERROR_FILE = args.state.with_suffix(".error.txt")
    if datetime.strptime(args.ttl, "%d-%m-%y").date() < datetime.now(timezone.utc).date():
        p.error("expired TTL")
    provider = SGProvider(args.manifest)
    manifest = provider.manifest
    account = manifest["account"]
    scope_hash = digest(manifest)
    state = json.loads(args.state.read_text()) if args.state.exists() else {
        "account": account, "scope_hash": scope_hash, "name": "aws-secops-ssh-dev-" + scope_hash[:10]
    }
    replacing = state["scope_hash"] != scope_hash
    if (state["account"] != account or not state["name"].startswith("aws-secops-ssh-dev-")
            or (replacing and not args.replace_scope)):
        p.error("existing SG deployment differs")
    print("PLAN=2 roles, 1 Lambda/log group, 1 Gateway/target, 1 Policy engine/policy; exact SG manifest only")
    if not args.create:
        return 0

    args.state.parent.mkdir(parents=True, exist_ok=True)
    name = state["name"]

    def save():
        temp = args.state.with_suffix(".new")
        with temp.open("w") as out:
            json.dump(state, out); out.flush(); os.fsync(out.fileno())
        temp.replace(args.state)

    def record(key, value):
        state[key] = value; save(); print("RECORDED=" + key, flush=True)

    tags = dict(Name=name, owner="amit", project="aws-secops", environment="dev",
                purpose="exact governed restricted-ssh demo", phase="inline-ssh", version="r01",
                created=datetime.now(timezone.utc).date().isoformat(), TTL=args.ttl,
                tools="chatgpt+codex", cleanup="review")

    for role, principal in [("lambdaRole", "lambda.amazonaws.com"), ("gatewayRole", "bedrock-agentcore.amazonaws.com")]:
        if role not in state:
            trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": principal}, "Action": "sts:AssumeRole"}]}
            if role == "gatewayRole":
                trust["Statement"][0]["Condition"] = {"StringEquals": {"aws:SourceAccount": account}}
            record(role, aws("iam", "create-role", role_name=name + "-" + role,
                             assume_role_policy_document=trust,
                             tags=[{"Key": k, "Value": v} for k, v in tags.items()])["Role"]["Arn"])

    log_name = "/aws/lambda/" + name
    if "logGroup" not in state:
        aws("logs", "create-log-group", log_group_name=log_name, tags=tags)
        record("logGroup", log_name)
    aws("logs", "put-retention-policy", log_group_name=log_name, retention_in_days=7)

    group_arns = [f"arn:aws:ec2:{REGION}:{account}:security-group/{g['group_id']}" for g in manifest["security_groups"]]
    lambda_policy = {"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": ["ec2:DescribeSecurityGroups", "ec2:DescribeSecurityGroupRules", "ec2:DescribeNetworkInterfaces"], "Resource": "*"},
        {"Effect": "Allow", "Action": "ec2:RevokeSecurityGroupIngress", "Resource": group_arns},
        {"Effect": "Allow", "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
         "Resource": f"arn:aws:logs:{REGION}:{account}:log-group:{log_name}:*"},
    ]}
    aws("iam", "put-role-policy", role_name=name + "-lambdaRole", policy_name="ExactScope", policy_document=lambda_policy)

    archive = args.state.with_suffix(".lambda.zip")
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as out:
        out.write(Path(__file__).resolve().parents[1] / "pilot_v1/sg_lambda.py", "sg_lambda.py")
        out.writestr("scope.json", json.dumps({**manifest, "scope_hash": scope_hash}))
    if "lambdaArn" not in state:
        time.sleep(10)
        record("lambdaArn", aws("lambda", "create-function", function_name=name, role=state["lambdaRole"],
                                runtime="python3.12", handler="sg_lambda.lambda_handler", timeout=60, memory_size=128,
                                zip_file="fileb://" + str(archive.resolve()), tags=tags)["FunctionArn"])
    elif replacing:
        aws("lambda", "update-function-code", function_name=name, zip_file="fileb://" + str(archive.resolve()))
        wait(lambda: aws("lambda", "get-function-configuration", function_name=name), "LastUpdateStatus", "Successful")
    wait(lambda: aws("lambda", "get-function-configuration", function_name=name), "State", "Active")

    if "policyEngineId" not in state:
        engine = aws("bedrock-agentcore-control", "create-policy-engine", name=name.replace("-", "_"), tags=tags)
        state.update({k: engine[k] for k in ("policyEngineId", "policyEngineArn")}); save()
    wait(lambda: aws("bedrock-agentcore-control", "get-policy-engine", policy_engine_id=state["policyEngineId"]), "status", "ACTIVE")

    gateway_policy = {"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": "lambda:InvokeFunction", "Resource": state["lambdaArn"]},
        {"Effect": "Allow", "Action": ["bedrock-agentcore:GetPolicyEngine", "bedrock-agentcore:AuthorizeAction", "bedrock-agentcore:PartiallyAuthorizeActions"],
         "Resource": [state["policyEngineArn"]] + ([state["gatewayArn"]] if "gatewayArn" in state else [])},
    ]}
    aws("iam", "put-role-policy", role_name=name + "-gatewayRole", policy_name="ExactScope", policy_document=gateway_policy)

    if "gatewayId" not in state:
        gateway = aws("bedrock-agentcore-control", "create-gateway", name=name, role_arn=state["gatewayRole"],
                      protocol_type="MCP", authorizer_type="AWS_IAM", tags=tags)
        state.update({k: gateway[k] for k in ("gatewayId", "gatewayArn", "gatewayUrl")}); save()
        gateway_policy["Statement"][1]["Resource"].append(state["gatewayArn"])
        aws("iam", "put-role-policy", role_name=name + "-gatewayRole", policy_name="ExactScope", policy_document=gateway_policy)
    wait(lambda: aws("bedrock-agentcore-control", "get-gateway", gateway_identifier=state["gatewayId"]), "status", "READY")

    enforced = {"arn": state["policyEngineArn"], "mode": "ENFORCE"}
    current = aws("bedrock-agentcore-control", "get-gateway", gateway_identifier=state["gatewayId"])
    if current.get("policyEngineConfiguration") != enforced:
        aws("bedrock-agentcore-control", "update-gateway", gateway_identifier=state["gatewayId"], name=name,
            role_arn=state["gatewayRole"], protocol_type="MCP", authorizer_type="AWS_IAM",
            policy_engine_configuration=enforced)
        current = wait(lambda: aws("bedrock-agentcore-control", "get-gateway", gateway_identifier=state["gatewayId"]), "status", "READY")
    if current.get("policyEngineConfiguration") != enforced:
        raise RuntimeError("ENFORCE missing; target not created")

    schema = {"name": "remove_unrestricted_ssh",
              "description": "Remove exact TCP/22 0.0.0.0/0 from one allowlisted unattached demo Security Group.",
              "inputSchema": {"type": "object", "properties": {
                  "scope_hash": {"type": "string"}, "resource_index": {"type": "integer"},
                  "batch_id": {"type": "string"}, "environment": {"type": "string"}},
                  "required": ["scope_hash", "resource_index", "batch_id", "environment"]}}
    if "targetId" not in state:
        target = aws("bedrock-agentcore-control", "create-gateway-target", gateway_identifier=state["gatewayId"],
                     name="ExactRestrictedSsh",
                     target_configuration={"mcp": {"lambda": {"lambdaArn": state["lambdaArn"],
                                                               "toolSchema": {"inlinePayload": [schema]}}}},
                     credential_provider_configurations=[{"credentialProviderType": "GATEWAY_IAM_ROLE"}])
        record("targetId", target["targetId"])
    wait(lambda: aws("bedrock-agentcore-control", "get-gateway-target", gateway_identifier=state["gatewayId"],
                     target_id=state["targetId"]), "status", "READY")

    state["toolName"] = "ExactRestrictedSsh___remove_unrestricted_ssh"
    statement = ('permit(principal, action == AgentCore::Action::"' + state["toolName"] + '", resource == AgentCore::Gateway::"' + state["gatewayArn"] + '") '
                 'when { context.input.environment == "dev" && context.input.scope_hash == "' + scope_hash + '" && '
                 'context.input.resource_index >= 0 && context.input.resource_index < ' + str(len(manifest["security_groups"])) + ' };')
    state["definition"] = {"cedar": {"statement": statement}}; save()
    if "policyId" not in state:
        record("policyId", aws("bedrock-agentcore-control", "create-policy", policy_engine_id=state["policyEngineId"],
                               name="exact_restricted_ssh_dev", definition=state["definition"],
                               validation_mode="FAIL_ON_ANY_FINDINGS", enforcement_mode="ACTIVE")["policyId"])
    elif replacing:
        aws("bedrock-agentcore-control", "update-policy", policy_engine_id=state["policyEngineId"], policy_id=state["policyId"],
            definition=state["definition"], validation_mode="FAIL_ON_ANY_FINDINGS", enforcement_mode="ACTIVE")
    wait(lambda: aws("bedrock-agentcore-control", "get-policy", policy_engine_id=state["policyEngineId"], policy_id=state["policyId"]),
         "status", "ACTIVE", {"definition": state["definition"]})
    state["scope_hash"] = scope_hash; save()
    print("SG_DEPLOYMENT=READY; no SG remediation invoked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
