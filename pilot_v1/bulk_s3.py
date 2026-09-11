"""Exact manifest-bound empty-bucket BPA provider. No ambient-profile fallback."""
import json
import os
import re
import random
import subprocess
import time
from pathlib import Path
from .bulk import TARGET, bpa, digest


class S3Provider:
    def __init__(self, manifest, *, sdk=False):
        if Path(str(manifest)+'.retired').exists():
            raise ValueError('manifest retired after writer migration; use the authoritative worker host')
        self.manifest = json.loads(Path(manifest).read_text())
        self.sdk = sdk
        self.clients = {}
        m = self.manifest
        if (m.get('version') != 1 or m.get('profile') != 'vagent' or m.get('region') != 'ap-southeast-1'
                or not re.fullmatch(r'\d{12}', m.get('account', ''))
                or not re.fullmatch(r'[a-f0-9]{16}', m.get('run', ''))
                or not 1 <= len(m.get('buckets', [])) <= 100):
            raise ValueError('invalid live manifest or scale gate')
        self.resources = list(m['buckets'])
        if len(set(self.resources)) != len(self.resources) or any(not re.fullmatch('aws-secops-bpa-'+m['run']+r'-\d{3}', r) for r in self.resources):
            raise ValueError('bucket manifest mismatch')
        self.context = dict(mode='LIVE', profile='vagent', region=m['region'], identity_hash=digest(m['account']), manifest_hash=digest(m))
        self.metrics = {'api_calls': 0, 'api_errors': 0, 'elapsed_seconds': 0, 'model_calls': 0}
        self.verify_identity()

    def call(self, service, operation, **args):
        if self.sdk and service in {'s3api', 'sts'}:
            return self.sdk_call(service, operation, args)
        cmd = ['aws', '--profile', 'vagent', '--region', 'ap-southeast-1', '--cli-connect-timeout', '5', '--cli-read-timeout', '15', service, operation]
        for key, value in args.items():
            cmd += ['--'+key.replace('_', '-'), json.dumps(value) if isinstance(value, (dict, list)) else str(value)]
        for attempt in range(3):
            start = time.monotonic(); self.metrics['api_calls'] += 1
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=35,
                                        env={**os.environ, 'AWS_MAX_ATTEMPTS': '1', 'AWS_PAGER': ''})
            except subprocess.TimeoutExpired:
                self.metrics['api_errors'] += 1
                raise RuntimeError('provider timeout; no blind retry') from None
            finally:
                self.metrics['elapsed_seconds'] += time.monotonic()-start
            throttled = result.returncode and any(s in result.stderr for s in ('Throttling', 'SlowDown', 'TooManyRequests'))
            if not throttled or not operation.startswith(('get-', 'list-', 'describe-')) or attempt == 2:
                break
            self.metrics['read_throttles'] = self.metrics.get('read_throttles', 0)+1
            time.sleep(random.uniform(0.25, 0.5)*(2**attempt))
        if result.returncode:
            # Error identifiers only; never surface raw account/resource/credential payloads.
            if 'NoSuchBucketPolicy' in result.stderr:
                return {'policy_absent': True}
            self.metrics['api_errors'] += 1
            raise RuntimeError('provider operation failed: '+operation)
        return json.loads(result.stdout or '{}')

    def sdk_call(self, service, operation, arguments):
        """Reuse official clients for fleet reads; no hidden SDK write retries."""
        if service not in self.clients:
            import boto3
            from botocore.config import Config
            self.clients[service] = boto3.Session(profile_name='vagent').client(
                's3' if service == 's3api' else service, region_name='ap-southeast-1',
                config=Config(connect_timeout=5, read_timeout=15, retries={'total_max_attempts': 1}))
        method = getattr(self.clients[service], operation.replace('-', '_'))
        parameters = {''.join(w.title() for w in k.split('_')): v for k,v in arguments.items()}
        for attempt in range(3):
            start = time.monotonic(); self.metrics['api_calls'] += 1
            try:
                return method(**parameters)
            except Exception as exc:
                code = getattr(exc, 'response', {}).get('Error', {}).get('Code', 'ProviderError')
                if code == 'NoSuchBucketPolicy': return {'policy_absent': True}
                if (code in {'Throttling','ThrottlingException','SlowDown','TooManyRequestsException'}
                        and operation.startswith(('get-','list-','describe-')) and attempt < 2):
                    self.metrics['read_throttles'] = self.metrics.get('read_throttles',0)+1
                    time.sleep(random.uniform(0.25,0.5)*(2**attempt))
                    continue
                self.metrics['api_errors'] += 1
                raise RuntimeError('provider operation failed: '+operation+'; '+code) from None
            finally:
                self.metrics['elapsed_seconds'] += time.monotonic()-start

    def verify_identity(self):
        if self.call('sts', 'get-caller-identity').get('Account') != self.manifest['account']:
            raise PermissionError('wrong live identity')

    def guard(self, resource):
        if resource not in self.resources:
            raise PermissionError('outside fixed manifest')
        self.verify_identity()
        args = dict(bucket=resource, expected_bucket_owner=self.manifest['account'])
        if self.call('s3api', 'get-bucket-location', **args).get('LocationConstraint') != 'ap-southeast-1':
            raise PermissionError('wrong bucket Region')
        tags = {t['Key']: t['Value'] for t in self.call('s3api', 'get-bucket-tagging', **args)['TagSet']}
        if any(tags.get(k) != v for k, v in {'project': 'aws-secops', 'owner': 'amit', 'phase': 'bulk-bpa', 'run': self.manifest['run']}.items()):
            raise PermissionError('ownership tags differ')
        versions = self.call('s3api', 'list-object-versions', **args, max_keys=1)
        if versions.get('Versions') or versions.get('DeleteMarkers') or versions.get('IsTruncated'):
            raise PermissionError('bucket not empty')
        if self.call('s3api', 'list-multipart-uploads', **args, max_uploads=1).get('Uploads'):
            raise PermissionError('multipart uploads present')
        ownership = self.call('s3api', 'get-bucket-ownership-controls', **args)
        if ownership.get('OwnershipControls', {}).get('Rules') != [{'ObjectOwnership': 'BucketOwnerEnforced'}]:
            raise PermissionError('ACLs not disabled')
        if self.call('s3api', 'get-bucket-policy', **args) != {'policy_absent': True}:
            raise PermissionError('bucket policy present')
        return args

    def read(self, resource):
        args = self.guard(resource)
        return bpa(self.call('s3api', 'get-public-access-block', **args)['PublicAccessBlockConfiguration'])

    def apply(self, resource, before):
        raise PermissionError('live remediation requires the governed Gateway provider')
