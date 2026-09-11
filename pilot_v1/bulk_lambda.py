"""Gateway-only exact BPA target. Private fixed manifest is packaged at deploy."""
import json
from pathlib import Path
import re

KEYS = ('BlockPublicAcls', 'IgnorePublicAcls', 'BlockPublicPolicy', 'RestrictPublicBuckets')
TARGET = dict.fromkeys(KEYS, True)


def remediate(s3, manifest, event):
    if (set(event) != {'scope_hash', 'resource_index', 'batch_id', 'environment'}
            or event['environment'] != 'dev' or event['scope_hash'] != manifest['scope_hash']
            or type(event['resource_index']) is not int
            or not 0 <= event['resource_index'] < len(manifest['buckets'])
            or not isinstance(event['batch_id'], str) or not re.fullmatch('[a-f0-9]{64}', event['batch_id'])):
        raise ValueError('outside exact governed scope')
    bucket = manifest['buckets'][event['resource_index']]
    args = dict(Bucket=bucket, ExpectedBucketOwner=manifest['account'])
    if s3.get_bucket_location(**args).get('LocationConstraint') != 'ap-southeast-1':
        raise ValueError('Region mismatch')
    tags = {x['Key']: x['Value'] for x in s3.get_bucket_tagging(**args)['TagSet']}
    if any(tags.get(k) != v for k, v in dict(project='aws-secops', owner='amit', phase='bulk-bpa', run=manifest['run']).items()):
        raise ValueError('ownership mismatch')
    contents = s3.list_object_versions(**args, MaxKeys=1)
    if contents.get('Versions') or contents.get('DeleteMarkers') or contents.get('IsTruncated'):
        raise ValueError('bucket not empty')
    if s3.list_multipart_uploads(**args, MaxUploads=1).get('Uploads'):
        raise ValueError('multipart present')
    if s3.get_bucket_ownership_controls(**args)['OwnershipControls']['Rules'] != [{'ObjectOwnership': 'BucketOwnerEnforced'}]:
        raise ValueError('ACLs not disabled')
    try:
        s3.get_bucket_policy(**args)
    except Exception as exc:
        if getattr(exc, 'response', {}).get('Error', {}).get('Code') != 'NoSuchBucketPolicy':
            raise
    else:
        raise ValueError('bucket policy present')
    before = s3.get_public_access_block(**args)['PublicAccessBlockConfiguration']
    if before == TARGET:
        return {'result': 'ALREADY_COMPLIANT', 'changed': False, 'scope_hash': event['scope_hash']}
    if before != {**TARGET, 'BlockPublicAcls': False}:
        raise ValueError('unexpected precondition; no write')
    s3.put_public_access_block(**args, PublicAccessBlockConfiguration=TARGET)
    return {'result': 'BPA_APPLIED', 'changed': True, 'scope_hash': event['scope_hash']}


def lambda_handler(event, context):
    custom = getattr(getattr(context, 'client_context', None), 'custom', {}) or {}
    if custom.get('bedrockAgentCoreToolName', '').rsplit('___', 1)[-1] != 'apply_bucket_bpa':
        raise ValueError('Gateway tool context required')
    import boto3
    from botocore.config import Config
    manifest = json.loads(Path(__file__).with_name('scope.json').read_text())
    # Never retry an uncertain write. Gateway invocation also has no client retry.
    s3 = boto3.client('s3', region_name='ap-southeast-1', config=Config(retries={'total_max_attempts': 1}, connect_timeout=5, read_timeout=10))
    return remediate(s3, manifest, event)
