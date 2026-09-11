import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from pilot_v1.bulk_s3 import S3Provider
from pilot_v1.bulk import TARGET


class BulkS3Tests(unittest.TestCase):
    def test_sdk_maps_owner_and_never_retries_writes(self):
        provider = object.__new__(S3Provider)
        client = Mock(); provider.clients = {'s3api': client}
        provider.metrics = dict(api_calls=0, api_errors=0, elapsed_seconds=0)
        provider.sdk_call('s3api','get-public-access-block',dict(bucket='owned',expected_bucket_owner='0'*12))
        client.get_public_access_block.assert_called_once_with(Bucket='owned',ExpectedBucketOwner='0'*12)
        error = RuntimeError(); error.response = {'Error': {'Code':'SlowDown'}}
        client.put_public_access_block.side_effect = error
        with self.assertRaises(RuntimeError):
            provider.sdk_call('s3api','put-public-access-block',dict(bucket='owned',public_access_block_configuration=TARGET))
        client.put_public_access_block.assert_called_once()

    def test_identity_manifest_and_scale_gate_before_dispatch(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'manifest.json'
            manifest = dict(version=1, profile='vagent', region='ap-southeast-1', account='0'*12,
                            run='a'*16, buckets=['aws-secops-bpa-'+'a'*16+'-000'])
            path.write_text(json.dumps(manifest))
            with patch.object(S3Provider, 'call', return_value={'Account': '1'*12}):
                with self.assertRaises(PermissionError): S3Provider(path)
            for key, value in [('profile', 'amit'), ('region', 'us-east-1'), ('buckets', ['unrelated'])]:
                path.write_text(json.dumps({**manifest, key: value}))
                with patch.object(S3Provider, 'call') as call:
                    with self.assertRaises(ValueError): S3Provider(path)
                    call.assert_not_called()

    def test_direct_write_fallback_removed(self):
        provider = object.__new__(S3Provider)
        provider.manifest = {'account': '0'*12}
        before = {**TARGET, 'BlockPublicAcls': False}
        with patch.object(provider, 'read', return_value=before), patch.object(provider, 'call') as call:
            with self.assertRaises(PermissionError): provider.apply('demo', before)
            call.assert_not_called()
        with patch.object(provider, 'read', return_value=TARGET), patch.object(provider, 'call') as call:
            with self.assertRaises(PermissionError): provider.apply('demo', before)
            call.assert_not_called()

    def test_outside_manifest_never_calls_aws(self):
        provider = object.__new__(S3Provider); provider.resources = ['owned']
        with patch.object(provider, 'call') as call:
            with self.assertRaises(PermissionError): provider.guard('other')
            call.assert_not_called()
