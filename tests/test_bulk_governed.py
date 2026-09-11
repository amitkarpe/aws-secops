import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
from pilot_v1.bulk import BulkStore, OfflineProvider, PolicyDenied, TARGET
from pilot_v1.bulk_gateway import GovernedS3Provider
from pilot_v1.bulk_lambda import remediate


class GovernedBulkTests(unittest.TestCase):
    def test_async_progress_exact_approval_and_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            provider = OfflineProvider(Path(tmp)/'provider', 2)
            store = BulkStore(Path(tmp)/'batch', provider)
            view = store.preview(); key = view['batch_id']
            entered = threading.Event(); release = threading.Event()
            apply = provider.apply
            def slow(resource, before):
                entered.set()
                if not release.wait(3): raise TimeoutError()
                return apply(resource, before)
            try:
                with patch.object(provider, 'apply', side_effect=slow):
                    with self.assertRaises(ValueError): store.start(key, 'forged')
                    self.assertEqual(provider.calls, 0)
                    store.start(key, key)
                    self.assertTrue(entered.wait(1))
                    self.assertTrue(store.summary()['execution_active'])
                    self.assertEqual(store.page(key)['summary']['counts']['RUNNING'], 1)
                    with self.assertRaises(ValueError): store.start(key, key)
                    release.set(); store.worker.join(3)
                self.assertEqual(store.summary()['verified'], 2)
                with self.assertRaises(ValueError): store.start(key, key)
                self.assertEqual(provider.calls, 2)
            finally:
                release.set(); store.close()

    def test_policy_denial_is_distinct_from_unknown_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            provider = OfflineProvider(Path(tmp)/'provider', 2)
            store = BulkStore(Path(tmp)/'batch', provider)
            try:
                key = store.preview()['batch_id']; store.decide(key, key, 'APPROVE')
                with patch.object(provider, 'apply', side_effect=PolicyDenied()): store.step(key)
                self.assertEqual(store.data['items'][0]['state'], 'DENIED')
                self.assertFalse(store.data['items'][0]['changed'])
                with patch.object(provider, 'apply', side_effect=TimeoutError()): store.step(key)
                self.assertEqual(store.data['items'][1]['state'], 'UNKNOWN')
                with self.assertRaises(ValueError): store.start(key, key)
                self.assertEqual(provider.calls, 0)
            finally: store.close()

    def test_exact_lambda_scope_and_postcondition(self):
        m = dict(scope_hash='a'*64, run='b'*16, buckets=['demo-owned'], account='0'*12)
        event = dict(scope_hash=m['scope_hash'], resource_index=0, batch_id='c'*64, environment='dev')
        s3 = Mock()
        s3.get_bucket_location.return_value = {'LocationConstraint': 'ap-southeast-1'}
        s3.get_bucket_tagging.return_value = {'TagSet': [{'Key': k, 'Value': v} for k,v in dict(project='aws-secops', owner='amit', phase='bulk-bpa', run=m['run']).items()]}
        s3.list_object_versions.return_value = {}; s3.list_multipart_uploads.return_value = {}
        s3.get_bucket_ownership_controls.return_value = {'OwnershipControls': {'Rules': [{'ObjectOwnership': 'BucketOwnerEnforced'}]}}
        absent = RuntimeError(); absent.response = {'Error': {'Code': 'NoSuchBucketPolicy'}}
        s3.get_bucket_policy.side_effect = absent
        s3.get_public_access_block.return_value = {'PublicAccessBlockConfiguration': {**TARGET, 'BlockPublicAcls': False}}
        for bad in [{**event, 'environment': 'prod'}, {**event, 'resource_index': True}, {**event, 'resource_index': 1}, {**event, 'bucket': 'outside'}, {**event, 'scope_hash': '0'*64}]:
            with self.assertRaises(ValueError): remediate(s3, m, bad)
        s3.put_public_access_block.assert_not_called()
        self.assertEqual(remediate(s3, m, event)['result'], 'BPA_APPLIED')
        s3.put_public_access_block.assert_called_once_with(Bucket='demo-owned', ExpectedBucketOwner='0'*12, PublicAccessBlockConfiguration=TARGET)

    def test_only_explicit_gateway_error_counts_as_policy_deny(self):
        provider = object.__new__(GovernedS3Provider)
        provider.resources = ['demo']; provider.batch_id = 'a'*64
        provider.deployment = dict(scope_hash='b'*64, gatewayUrl='unused', toolName='ExactBpa___apply_bucket_bpa')
        provider.metrics = dict(gateway_calls=0, policy_denied=0)
        with patch('pilot_v1.bulk_gateway.call_tool', return_value={'error': {'code': -32002, 'message': 'Tool Execution Denied: denied by default'}}):
            with self.assertRaises(PolicyDenied): provider.invoke('demo')
        with patch('pilot_v1.bulk_gateway.call_tool', return_value={'error': {'code': -32000, 'message': 'timeout'}}):
            with self.assertRaises(RuntimeError): provider.invoke('demo')
        self.assertEqual(provider.metrics['policy_denied'], 1)


if __name__ == '__main__': unittest.main()
