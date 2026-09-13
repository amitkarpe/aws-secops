#!/usr/bin/env python3
"""No-change live AgentCore Policy DENY/ALLOW probe for the SG target."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pilot_v1.bulk import PolicyDenied
from pilot_v1.log_proof import count_lambda_starts
from pilot_v1.sg_compliance import GovernedSGProvider, TARGET, digest

p = argparse.ArgumentParser()
p.add_argument("--manifest", type=Path, required=True)
p.add_argument("--gateway-state", type=Path, required=True)
p.add_argument("--verify-logs", action="store_true")
a = p.parse_args()
provider = GovernedSGProvider(a.manifest, a.gateway_state)
resource = provider.resources[0]
if provider.read(resource) != TARGET:
    raise RuntimeError("probe requires an already-compliant SG; no mutation allowed")
provider.authorize(digest({"probe": "sg-policy-only", "scope": provider.context}))
start_ms = int(time.time() * 1000)
try:
    provider.invoke(resource, environment="prod")
except PolicyDenied:
    print("POLICY_DENY=PASS", flush=True)
else:
    raise RuntimeError("Policy DENY not proven")
denied_end = int(time.time() * 1000)
if provider.read(resource) != TARGET:
    raise RuntimeError("unexpected provider change after DENY")
allowed = provider.invoke(resource, environment="dev")
if allowed["target_result"] != "ALREADY_COMPLIANT" or provider.read(resource) != TARGET:
    raise RuntimeError("no-change ALLOW not proven")
print("POLICY_ALLOW=PASS TARGET=ALREADY_COMPLIANT AWS_MUTATION=NONE", flush=True)
end_ms = int(time.time() * 1000)

if a.verify_logs:
    import boto3
    from botocore.config import Config
    logs = boto3.Session(profile_name="vagent").client(
        "logs", region_name="ap-southeast-1",
        config=Config(connect_timeout=5, read_timeout=15, retries={"total_max_attempts": 2}),
    )
    log_group = provider.deployment["logGroup"]
    for _ in range(12):
        denied_calls = count_lambda_starts(logs, log_group, start_ms, denied_end)
        allowed_calls = count_lambda_starts(logs, log_group, denied_end, end_ms)
        if denied_calls or allowed_calls > 1:
            raise RuntimeError("unexpected Lambda execution count")
        if allowed_calls == 1:
            break
        time.sleep(5)
    else:
        raise RuntimeError("bounded Lambda log evidence unavailable")
    print("LAMBDA_START_RECORDS DENY=0 ALLOW=1", flush=True)
