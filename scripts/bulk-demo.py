#!/usr/bin/env python3
"""Explicit empty demo factory/reset/cleanup; never executes an approval batch."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pilot_v1.bulk import TARGET, digest
from pilot_v1.bulk_s3 import S3Provider


def main():
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['create', 'grow', 'read', 'reset', 'cleanup'])
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--account-file', type=Path, help='private preflight STS JSON, create only')
    p.add_argument('--count', type=int, default=5, choices=[5, 10, 50, 100])
    p.add_argument('--ttl', help='explicit review date DD-MM-YY')
    p.add_argument('--batch-state', type=Path, help='batch journal used by the demo server')
    a = p.parse_args(); os.umask(0o077)
    if a.action == 'grow':
        if not a.batch_state or not a.ttl:
            p.error('growth requires terminal current journal and TTL')
        from datetime import datetime, timezone
        if datetime.strptime(a.ttl,'%d-%m-%y').date() < datetime.now(timezone.utc).date(): p.error('expired TTL')
        lease = open(str(a.batch_state)+'.lock','a')
        fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        old = json.loads(a.manifest.read_text()); saved = json.loads(a.batch_state.read_text())
        count = len(old['buckets'])
        if ({5:10,10:50,50:100}.get(count) != a.count or saved['manifest']['context']['manifest_hash'] != digest(old)
                or len(saved['items']) != count or any(i['state'] not in {'COMPLETED','SKIPPED'} for i in saved['items'])):
            p.error('only proven terminal 5->10->50->100 growth; no jump/replay')
        provider = S3Provider(a.manifest, sdk=os.environ.get('SECOPS_BULK_SDK') == '1')
        # Quota and Free Tier metadata are global endpoints, not resource Regions.
        def metadata(service, operation, extra):
            r = subprocess.run(['aws','--profile','vagent','--region','us-east-1',service,operation,*extra],capture_output=True,text=True,timeout=35,check=True)
            return json.loads(r.stdout)
        quota = metadata('service-quotas','get-service-quota',['--service-code','s3','--quota-code','L-DC2B2D3D'])['Quota']['Value']
        plan = metadata('freetier','get-account-plan-state',[])
        used = len(provider.call('s3api','list-buckets')['Buckets'])
        if quota < used+a.count-count or plan.get('accountPlanStatus') != 'ACTIVE':
            p.error('quota/plan readiness failed')
        print('SCALE_PREFLIGHT='+json.dumps(dict(quota=quota,used=used,next=a.count,plan=plan['accountPlanType'],credit_balance='not inferred')),flush=True)
        for bucket in old['buckets']:
            if provider.read(bucket) != TARGET: p.error('previous fleet not provider compliant')
        new = {**old,'buckets':[f'aws-secops-bpa-{old["run"]}-{i:03d}' for i in range(a.count)]}
        backup = a.manifest.with_name(a.manifest.name+f'.before-{a.count}')
        with backup.open('x') as out: json.dump(old,out)
        a.manifest.write_text(json.dumps(new))
        provider = S3Provider(a.manifest, sdk=os.environ.get('SECOPS_BULK_SDK') == '1')
        for bucket in new['buckets'][count:]:
            provider.call('s3api','create-bucket',bucket=bucket,create_bucket_configuration={'LocationConstraint':'ap-southeast-1'},object_ownership='BucketOwnerEnforced')
            tags=dict(Name=bucket,owner='amit',dev='amit',project='aws-secops',phase='bulk-bpa',run=new['run'],version='r01',environment='dev',tools='cdx',TTL=a.ttl,cleanup='review',purpose='empty BPA compliance demo',created=datetime.now(timezone.utc).date().isoformat())
            provider.call('s3api','put-bucket-tagging',bucket=bucket,expected_bucket_owner=new['account'],tagging={'TagSet':[{'Key':k,'Value':v} for k,v in tags.items()]})
            print('OWNED_EMPTY_BUCKET_CREATED',flush=True)
        # Existing and newly created empty buckets: same controlled reset only.
        for bucket in new['buckets']:
            args = provider.guard(bucket)
            provider.call('s3api','put-public-access-block',**args,public_access_block_configuration={**TARGET,'BlockPublicAcls':False})
            if provider.read(bucket) != {**TARGET,'BlockPublicAcls':False}: raise RuntimeError('growth readback failed')
            print('RESET_AND_READBACK=PASS',flush=True)
        print('GROWN='+str(a.count)); print(json.dumps(provider.metrics)); return
    if a.action == 'create':
        if a.manifest.exists() or not a.account_file or not a.ttl or a.count > 10:
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
        provider = S3Provider(a.manifest, sdk=os.environ.get('SECOPS_BULK_SDK') == '1')
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
        provider = S3Provider(a.manifest, sdk=os.environ.get('SECOPS_BULK_SDK') == '1')
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
