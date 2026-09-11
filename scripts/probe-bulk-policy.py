#!/usr/bin/env python3
"""No-change live Policy probe: existing compliant S3 resources only."""
import argparse
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pilot_v1.bulk import PolicyDenied, TARGET, digest
from pilot_v1.bulk_gateway import GovernedS3Provider
from pilot_v1.log_proof import count_lambda_starts

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
    import boto3
    from botocore.config import Config
    logs = boto3.Session(profile_name='vagent').client(
        'logs', region_name='ap-southeast-1',
        config=Config(connect_timeout=5, read_timeout=15, retries={'total_max_attempts': 2}),
    )
    for _ in range(12):
        denied_calls = count_lambda_starts(logs, provider.deployment['logGroup'], start_ms, denied_window_end)
        allowed_calls = count_lambda_starts(logs, provider.deployment['logGroup'], denied_window_end, end_ms)
        if denied_calls or allowed_calls > 1:
            raise RuntimeError('unexpected Lambda execution count')
        if allowed_calls == 1:
            break
        time.sleep(5)
    else:
        raise RuntimeError('bounded Lambda log evidence unavailable')
    print('LAMBDA_START_RECORDS DENY=0 ALLOW=1; bounded independent log proof',flush=True)
