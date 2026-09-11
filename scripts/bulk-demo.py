#!/usr/bin/env python3
"""Explicit empty demo factory/reset/cleanup; never executes an approval batch."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import secrets
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pilot_v1.bulk import TARGET
from pilot_v1.bulk_s3 import S3Provider


def main():
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['create', 'read', 'reset', 'cleanup'])
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--account-file', type=Path, help='private preflight STS JSON, create only')
    p.add_argument('--count', type=int, default=5, choices=range(5, 11))
    p.add_argument('--ttl', help='explicit review date DD-MM-YY')
    p.add_argument('--batch-state', type=Path, help='batch journal used by the demo server')
    a = p.parse_args(); os.umask(0o077)
    if a.action == 'create':
        if a.manifest.exists() or not a.account_file or not a.ttl:
            p.error('create requires new manifest, verified account-file and TTL')
        account = json.loads(a.account_file.read_text())['Account']
        from datetime import datetime, timezone
        if datetime.strptime(a.ttl, '%d-%m-%y').date() < datetime.now(timezone.utc).date():
            p.error('TTL must not be expired')
        run = secrets.token_hex(8)
        m = dict(version=1, profile='vagent', region='ap-southeast-1', account=account,
                 run=run, buckets=[f'aws-secops-bpa-{run}-{i:03d}' for i in range(a.count)])
        a.manifest.parent.mkdir(parents=True, exist_ok=True)
        with a.manifest.open('x') as out:
            json.dump(m, out)
        provider = S3Provider(a.manifest)
        for bucket in provider.resources:
            provider.call('s3api', 'create-bucket', bucket=bucket,
                          create_bucket_configuration={'LocationConstraint': 'ap-southeast-1'},
                          object_ownership='BucketOwnerEnforced')
            tags = dict(Name=bucket, owner='amit', dev='amit', project='aws-secops', phase='bulk-bpa',
                        run=run, version='r01', environment='dev', tools='cdx', TTL=a.ttl, cleanup='review',
                        purpose='empty BPA compliance demo', created=datetime.now(timezone.utc).date().isoformat())
            provider.call('s3api', 'put-bucket-tagging', bucket=bucket, expected_bucket_owner=account,
                          tagging={'TagSet': [{'Key': k, 'Value': v} for k, v in tags.items()]})
            # Only one bucket flag relaxed. ACLs stay disabled; no policy/objects.
            provider.guard(bucket)
            provider.call('s3api', 'put-public-access-block', bucket=bucket, expected_bucket_owner=account,
                          public_access_block_configuration={**TARGET, 'BlockPublicAcls': False})
            if provider.read(bucket) != {**TARGET, 'BlockPublicAcls': False}:
                raise RuntimeError('creation readback failed')
        print('CREATED='+str(len(provider.resources)))
    else:
        lease = None
        if a.action in {'reset', 'cleanup'}:
            state = a.batch_state or a.manifest.with_name('demo-batch.json')
            lease = open(str(state)+'.lock', 'a')
            try:
                fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                p.error('stop the batch server before reset/cleanup')
            if state.exists():
                saved = json.loads(state.read_text())
                if any(i['state'] in {'PENDING', 'APPROVED', 'RUNNING', 'UNKNOWN'} for i in saved['items']):
                    p.error('current batch must be terminal before reset/cleanup')
        provider = S3Provider(a.manifest)
        for bucket in provider.resources:
            args = provider.guard(bucket)
            if a.action == 'reset':
                provider.call('s3api', 'put-public-access-block', **args,
                              public_access_block_configuration={**TARGET, 'BlockPublicAcls': False})
                if provider.read(bucket) != {**TARGET, 'BlockPublicAcls': False}:
                    raise RuntimeError('reset readback failed')
            elif a.action == 'cleanup':
                provider.call('s3api', 'delete-bucket', **args)
            else:
                print('COMPLIANT' if provider.read(bucket) == TARGET else 'NON_COMPLIANT')
        if a.action == 'cleanup':
            existing = {b['Name'] for b in provider.call('s3api', 'list-buckets')['Buckets']}
            if existing.intersection(provider.resources):
                raise RuntimeError('cleanup readback failed')
            print('DELETION_READBACK=PASS')
        print('RESULT='+a.action.upper()+' COUNT='+str(len(provider.resources)))
    print(json.dumps(provider.metrics))


if __name__ == '__main__':
    main()
