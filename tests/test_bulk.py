import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from pilot_v1.bulk import BulkStore, OfflineProvider, TARGET


class BulkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.provider = OfflineProvider(self.root/'provider.json', 5)
        self.store = BulkStore(self.root/'bulk.json', self.provider)

    def tearDown(self):
        self.store.close(); self.temp.cleanup()

    def approve(self):
        view = self.store.preview()
        self.store.decide(view['batch_id'], view['approval_hash'], 'APPROVE')
        return view['batch_id']

    def test_reject_new_preview_hash_replay_and_scope(self):
        view = self.store.preview()
        page = self.store.page(view['batch_id'])
        self.assertFalse(page['items'][0]['before']['BlockPublicAcls'])
        page['items'][0]['before']['BlockPublicAcls'] = True
        self.assertFalse(self.store.page(view['batch_id'])['items'][0]['before']['BlockPublicAcls'])
        with self.assertRaises(ValueError):
            self.store.decide(view['batch_id'], 'forged', 'APPROVE')
        self.store.decide(view['batch_id'], view['approval_hash'], 'REJECT')
        with self.assertRaises(ValueError): self.store.step(view['batch_id'])
        new = self.store.preview(renew=True)
        self.assertNotEqual(new['approval_hash'], view['approval_hash'])
        with self.assertRaises(ValueError): self.store.decide(view['batch_id'], view['approval_hash'], 'APPROVE')
        self.assertEqual(self.provider.calls, 0)
        self.store.data['manifest']['target']['BlockPublicAcls'] = False
        with self.assertRaises(ValueError): self.store.step(new['batch_id'])

    def test_mixed_and_replay(self):
        key = self.approve()
        resources = self.provider.resources
        self.provider.values[resources[0]] = dict(TARGET)
        self.provider.values[resources[1]]['IgnorePublicAcls'] = False
        while self.store.summary()['counts'].get('APPROVED'):
            self.store.step(key)
        self.assertEqual(self.store.summary()['counts'], {'SKIPPED': 1, 'DENIED': 1, 'COMPLETED': 3})
        self.store.step(key)
        self.assertEqual(self.provider.calls, 3)
        with self.assertRaises(ValueError): self.store.decide(key, key, 'APPROVE')

    def test_restart_expires_unclaimed_approval_after_running_item(self):
        key = self.approve()
        with self.assertRaises(RuntimeError): BulkStore(self.root/'bulk.json', self.provider)
        self.store.data['items'][0]['state'] = 'RUNNING'; self.store.save()
        self.store.close(); self.store = BulkStore(self.root/'bulk.json', self.provider)
        self.assertEqual(self.store.data['items'][0]['state'], 'UNKNOWN')
        self.assertTrue(all(item['state'] == 'FAILED' for item in self.store.data['items'][1:]))
        self.assertEqual(self.provider.calls, 0)
        self.store.reconcile(key)
        self.assertEqual(self.store.data['items'][0]['state'], 'FAILED')
        self.assertIsNone(self.store.data['items'][0]['changed'])
        self.assertEqual(self.provider.calls, 0)
        with self.assertRaisesRegex(ValueError, 'cannot replay'):
            self.store.start(key, key)

    def test_thread_start_failure_expires_all_unclaimed_work(self):
        key = self.approve()
        with patch('pilot_v1.bulk.threading.Thread.start', side_effect=RuntimeError('launch failed')):
            with self.assertRaisesRegex(RuntimeError, 'no dispatch'):
                self.store.start(key, key)
        self.assertTrue(all(item['state'] == 'FAILED' for item in self.store.data['items']))
        self.assertTrue(all(item['changed'] is False and item['after'] is None
                            for item in self.store.data['items']))
        self.assertEqual(self.provider.calls, 0)
        with self.assertRaisesRegex(ValueError, 'cannot replay'):
            self.store.start(key, key)

    def test_uncertain_dispatch_expires_remaining_approval_without_replay(self):
        key = self.approve()
        with patch.object(self.provider, 'apply', side_effect=TimeoutError('uncertain')) as apply:
            self.store._run(key)
        self.assertEqual(apply.call_count, 1)
        self.assertEqual(self.store.data['items'][0]['state'], 'UNKNOWN')
        self.assertTrue(all(item['state'] == 'FAILED' for item in self.store.data['items'][1:]))
        self.store.reconcile(key)
        self.assertEqual(apply.call_count, 1)
        self.assertEqual(self.store.data['items'][0]['state'], 'FAILED')
        with self.assertRaisesRegex(ValueError, 'cannot replay'):
            self.store.start(key, key)

    def test_failure_before_and_after_dispatch(self):
        key = self.approve()
        with patch.object(self.provider, 'read', side_effect=RuntimeError('offline')):
            self.store.step(key)
        self.assertEqual(self.provider.calls, 0)
        with patch.object(self.provider, 'apply', side_effect=TimeoutError()):
            self.store.step(key)
        self.assertEqual(self.store.data['items'][1]['state'], 'UNKNOWN')

    def test_offline_1000_durable_scale(self):
        self.store.close()
        provider = OfflineProvider(self.root/'scale-provider.json', 1000)
        self.store = BulkStore(self.root/'scale.json', provider)
        started = time.monotonic()
        key = self.approve()
        for _ in range(1000): self.store.step(key)
        self.assertEqual(self.store.summary()['verified'], 1000)
        self.assertEqual(provider.calls, 1000)
        self.assertEqual(len(self.store.page(key)['items']), 20)
        self.assertEqual(len(self.store.export(key).splitlines()), 1001)
        self.store.close(); self.store = BulkStore(self.root/'scale.json', provider)
        self.assertEqual(self.store.summary()['verified'], 1000)
        print('OFFLINE_1000_SECONDS=%.3f' % (time.monotonic()-started))

    def test_corrupt_store_stops_without_overwrite(self):
        self.store.close()
        path = self.root/'bulk.json'; path.write_text('{bad')
        with self.assertRaises(RuntimeError): BulkStore(path, self.provider)
        self.assertEqual(path.read_text(), '{bad')


    def test_verification_time_is_a_recorded_event_not_file_mtime(self):
        from pilot_v1.operator_server import OperatorService
        import os
        key = self.approve()
        while self.store.summary()['counts'].get('APPROVED'):
            self.store.step(key)
        stamp = self.store.summary()['last_verification_time']
        self.assertIsInstance(stamp, str)
        self.assertTrue(all(i.get('verified_at') for i in self.store.data['items']))
        service = OperatorService(self.store)
        service._config_control = lambda _: {'counts': {'COMPLIANT': 5}, 'partial': False}
        os.utime(self.store.path, (1, 1))
        self.assertEqual(service.s3_status()['last_verification_time'], stamp)
        self.assertIn('not a fresh scan', service.s3_status()['evidence_source'])
        self.store.close()
        self.store = BulkStore(self.root/'bulk.json', self.provider)
        self.assertEqual(self.store.summary()['last_verification_time'], stamp)

    def test_legacy_journal_keeps_unknown_verification_timestamp(self):
        from pilot_v1.operator_server import OperatorService
        key = self.approve()
        while self.store.summary()['counts'].get('APPROVED'):
            self.store.step(key)
        for item in self.store.data['items']:
            item.pop('verified_at', None)
        self.store.save()
        service = OperatorService(self.store)
        service._config_control = lambda _: {'counts': {'COMPLIANT': 5}}
        status = service.s3_status()
        self.assertEqual(status['compliant'], 5)
        self.assertIsNone(status['last_verification_time'])

    def test_readonly_reconciliation_refuses_an_inflight_item(self):
        key = self.approve()
        self.store.data['items'][0]['state'] = 'RUNNING'
        self.store.data['items'][1]['state'] = 'UNKNOWN'
        self.store.save()
        with self.assertRaisesRegex(ValueError, 'active'):
            self.store.reconcile(key)
        self.assertEqual(self.provider.calls, 0)


if __name__ == '__main__': unittest.main()
