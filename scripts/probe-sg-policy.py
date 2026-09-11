#!/usr/bin/env python3
"""No-change live AgentCore Policy DENY/ALLOW probe for the SG target."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pilot_v1.bulk import PolicyDenied
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
    import os, subprocess
    d = provider.deployment
    def starts(begin, end):
        cmd = ["aws", "--profile", "vagent", "--region", "ap-southeast-1", "logs", "filter-log-events",
               "--log-group-name", d["logGroup"], "--start-time", str(begin), "--end-time", str(end),
               "--filter-pattern", "\"START RequestId:\"", "--output", "json", "--no-paginate"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                                env={**os.environ, "AWS_MAX_ATTEMPTS": "1", "AWS_PAGER": ""})
        if result.returncode:
            raise RuntimeError("log proof unavailable")
        value = json.loads(result.stdout)
        if value.get("nextToken"):
            raise RuntimeError("unexpected paginated log proof")
        return len(value.get("events", []))
    for _ in range(12):
        denied_calls, allowed_calls = starts(start_ms, denied_end), starts(denied_end, end_ms)
        if denied_calls or allowed_calls > 1:
            raise RuntimeError("unexpected Lambda execution count")
        if allowed_calls == 1:
            break
        time.sleep(5)
    else:
        raise RuntimeError("bounded Lambda log evidence unavailable")
    print("LAMBDA_START_RECORDS DENY=0 ALLOW=1", flush=True)
