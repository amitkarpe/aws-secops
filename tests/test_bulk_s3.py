import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from pilot_v1.bulk_s3 import S3Provider
from pilot_v1.bulk import TARGET


class BulkS3Tests(unittest.TestCase):
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

    def test_exact_put_and_stale_evidence_block(self):
        provider = object.__new__(S3Provider)
        provider.manifest = {'account': '0'*12}
        before = {**TARGET, 'BlockPublicAcls': False}
        with patch.object(provider, 'read', return_value=before), patch.object(provider, 'call') as call:
            provider.apply('demo', before)
            call.assert_called_once_with('s3api', 'put-public-access-block', bucket='demo',
                                         expected_bucket_owner='0'*12, public_access_block_configuration=TARGET)
        with patch.object(provider, 'read', return_value=TARGET), patch.object(provider, 'call') as call:
            with self.assertRaises(PermissionError): provider.apply('demo', before)
            call.assert_not_called()

    def test_outside_manifest_never_calls_aws(self):
        provider = object.__new__(S3Provider); provider.resources = ['owned']
        with patch.object(provider, 'call') as call:
            with self.assertRaises(PermissionError): provider.guard('other')
            call.assert_not_called()
