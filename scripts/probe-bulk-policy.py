#!/usr/bin/env python3
"""No-change live Policy probe: existing compliant resources only."""
import argparse
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pilot_v1.bulk import PolicyDenied, TARGET, digest
from pilot_v1.bulk_gateway import GovernedS3Provider

p = argparse.ArgumentParser()
p.add_argument('--manifest', type=Path, required=True)
p.add_argument('--gateway-state', type=Path, required=True)
p.add_argument('--verify-logs', action='store_true', help='bounded independent Lambda START counts')
a = p.parse_args()
provider = GovernedS3Provider(a.manifest, a.gateway_state)
resource = provider.resources[0]
if provider.read(resource) != TARGET:
    raise RuntimeError('probe requires already-compliant resource; no mutation allowed')
provider.authorize(digest({'probe': 'policy-only', 'scope': provider.context}))
start_ms = int(time.time()*1000)
try:
    provider.invoke(resource, environment='prod')
except PolicyDenied:
    print('POLICY_DENY=PASS', flush=True)
else:
    raise RuntimeError('Policy DENY not proven')
if provider.read(resource) != TARGET:
    raise RuntimeError('unexpected provider change')
denied_window_end = int(time.time()*1000)
allowed = provider.invoke(resource)
if allowed['target_result'] != 'ALREADY_COMPLIANT' or provider.read(resource) != TARGET:
    raise RuntimeError('no-change ALLOW not proven')
print('POLICY_ALLOW=PASS TARGET=ALREADY_COMPLIANT AWS_MUTATION=NONE', flush=True)
end_ms = int(time.time()*1000)
if a.verify_logs:
    def starts(begin, end):
        result = provider.call('logs','filter-log-events',log_group_name=provider.deployment['logGroup'],
                               start_time=begin,end_time=end,filter_pattern='"START RequestId:"')
        if result.get('nextToken'): raise RuntimeError('unexpected paginated probe logs')
        return len(result.get('events',[]))
    for _ in range(12):
        denied_calls, allowed_calls = starts(start_ms,denied_window_end), starts(denied_window_end,end_ms)
        if denied_calls or allowed_calls > 1: raise RuntimeError('unexpected Lambda execution count')
        if allowed_calls == 1: break
        time.sleep(5)
    else: raise RuntimeError('bounded Lambda log evidence unavailable')
    print('LAMBDA_START_RECORDS DENY=0 ALLOW=1; bounded independent log proof',flush=True)
print(json.dumps({'start_ms': start_ms, 'denied_window_end_ms': denied_window_end,
                  'end_ms': end_ms, 'metrics': provider.metrics}))
