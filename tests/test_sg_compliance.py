import tempfile
import time
from pathlib import Path
import unittest
from unittest.mock import patch

from pilot_v1.sg_compliance import SGBatchStore, TARGET
from pilot_v1.bulk import PolicyDenied


class FakeProvider:
    concurrency = 2
    context = {"mode": "LIVE", "profile": "vagent", "region": "ap-southeast-1", "family": "SECURITY_GROUP",
               "manifest_hash": "x", "identity_hash": "y", "governance_hash": "z"}

    def __init__(self):
        self.resources = ["sg-a1", "sg-b2", "sg-c3"]
        self.values = {x: {"unrestricted_ssh": True} for x in self.resources}
        self.metrics = {"api_calls": 0, "api_errors": 0, "gateway_calls": 0, "policy_denied": 0, "target_success": 0}
        self.authorized = []
        self.calls = []
        self.deny = set()

    def read(self, resource):
        if resource not in self.resources:
            raise PermissionError("outside")
        return dict(self.values[resource])

    def authorize(self, batch_id):
        self.authorized.append(batch_id)

    def apply(self, resource, before):
        self.calls.append(resource)
        if resource in self.deny:
            raise PolicyDenied("deny")
        if self.values[resource] != before:
            raise PermissionError("drift")
        self.values[resource] = dict(TARGET)
        return {"gateway_decision": "ALLOW", "target_result": "SSH_REVOKED", "target_calls": 1}


class SGBatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.provider = FakeProvider()
        self.path = Path(self.temp.name) / "sg.json"
        self.store = SGBatchStore(self.path, self.provider)

    def tearDown(self):
        self.store.close(); self.temp.cleanup()

    def wait(self):
        for _ in range(100):
            if not self.store.summary()["execution_active"]:
                return
            time.sleep(.01)
        self.fail("worker did not finish")

    def test_exact_approval_runs_and_terminal_replay_is_blocked(self):
        view = self.store.preview()
        self.store.start(view["batch_id"], view["approval_hash"])
        self.wait()
        summary = self.store.summary()
        self.assertEqual(summary["verified"], 3)
        self.assertEqual(summary["counts"], {"COMPLETED": 3})
        self.assertEqual(len(self.provider.calls), 3)
        with self.assertRaises(ValueError):
            self.store.start(view["batch_id"], view["approval_hash"])

    def test_stale_hash_and_provider_already_compliant_do_not_dispatch(self):
        view = self.store.preview()
        with self.assertRaises(ValueError):
            self.store.start(view["batch_id"], "f" * 64)
        self.provider.values["sg-a1"] = {"unrestricted_ssh": False}
        self.store.start(view["batch_id"], view["approval_hash"])
        self.wait()
        self.assertEqual(self.store.summary()["counts"].get("SKIPPED"), 1)
        self.assertNotIn("sg-a1", self.provider.calls)

    def test_policy_deny_is_distinct(self):
        self.provider.deny.add("sg-a1")
        view = self.store.preview()
        self.store.start(view["batch_id"], view["approval_hash"])
        self.wait()
        page = self.store.page(view["batch_id"], limit=10)
        denied = next(i for i in page["items"] if i["resource"] == "sg-a1")
        self.assertEqual(denied["state"], "DENIED")
        self.assertEqual(denied["audit"]["gateway_decision"], "DENY")

    def test_restart_running_becomes_unknown_then_readonly_reconcile(self):
        view = self.store.preview()
        self.store.data["decision"] = "APPROVE"
        self.store.data["items"][0]["state"] = "RUNNING"
        self.store.data["items"][1]["state"] = "APPROVED"
        self.store.data["items"][2]["state"] = "APPROVED"
        self.store.save()
        self.provider.values["sg-a1"] = {"unrestricted_ssh": False}
        self.store.close()
        self.store = SGBatchStore(self.path, self.provider)
        self.assertEqual(self.store.data["items"][0]["state"], "UNKNOWN")
        self.store.reconcile(view["batch_id"])
        self.assertEqual(self.store.data["items"][0]["state"], "COMPLETED")
        self.assertIsNone(self.store.data["items"][0]["changed"])
        self.assertFalse(self.provider.calls)

    def test_new_preview_archives_terminal_journal(self):
        view = self.store.preview()
        self.store.start(view["batch_id"], view["approval_hash"]); self.wait()
        new = self.store.preview(renew=True)
        self.assertNotEqual(view["batch_id"], new["batch_id"])
        self.assertTrue(self.path.with_name(self.path.name + "." + view["batch_id"]).exists())

    def test_interrupted_batch_terminates_unsent_work_and_keeps_history(self):
        original = self.store.preview()
        self.store.data["decision"] = "APPROVE"
        self.store.data["items"][0].update(state="RUNNING", changed=None)
        for item in self.store.data["items"][1:]:
            item["state"] = "APPROVED"
        self.store.save()
        self.provider.values["sg-a1"] = dict(TARGET)
        self.store.close()
        self.store = SGBatchStore(self.path, self.provider)
        self.assertEqual(self.store.summary()["counts"], {"UNKNOWN": 1, "FAILED": 2})
        for item in self.store.data["items"][1:]:
            self.assertFalse(item["changed"])
            self.assertIn("not dispatched", item["message"].lower())
        with self.assertRaises(ValueError):
            self.store.preview(renew=True)
        self.store.reconcile(original["batch_id"])
        self.assertEqual(self.store.summary()["counts"], {"COMPLETED": 1, "FAILED": 2})
        self.assertEqual(self.provider.calls, [])
        with self.assertRaises(ValueError):
            self.store.start(original["batch_id"], original["approval_hash"])
        # A new full-manifest preview is local planning, not approval. It keeps
        # the previous journal and needs a separate explicit start decision.
        new = self.store.preview(renew=True)
        archive = self.path.with_name(self.path.name + "." + original["batch_id"])
        self.assertTrue(archive.exists())
        self.assertNotEqual(original["batch_id"], new["batch_id"])
        self.assertEqual(new["counts"], {"PENDING": 3})
        self.assertEqual(self.provider.calls, [])
        self.store.start(new["batch_id"], new["approval_hash"])
        self.wait()
        self.assertEqual(self.store.summary()["verified"], 3)
        self.assertEqual(self.store.summary()["counts"], {"SKIPPED": 1, "COMPLETED": 2})
        self.assertNotIn("sg-a1", self.provider.calls)

    def test_unknown_dispatch_stops_and_terminalizes_unstarted_items(self):
        self.provider.concurrency = 1
        def uncertain(resource, before):
            self.provider.calls.append(resource)
            self.provider.values[resource] = dict(TARGET)
            raise TimeoutError("response lost after provider change")
        self.provider.apply = uncertain
        view = self.store.preview()
        self.store.start(view["batch_id"], view["approval_hash"])
        self.wait()
        self.assertEqual(self.store.summary()["counts"], {"UNKNOWN": 1, "FAILED": 2})
        self.assertEqual(len(self.provider.calls), 1)
        self.store.reconcile(view["batch_id"])
        self.assertEqual(self.store.summary()["counts"], {"COMPLETED": 1, "FAILED": 2})
        self.assertIsNone(self.store.data["items"][0]["changed"])
        self.assertEqual(len(self.provider.calls), 1)

    def test_reconciliation_cannot_race_active_execution(self):
        view = self.store.preview()
        self.store.data["decision"] = "APPROVE"
        self.store.data["items"][0]["state"] = "RUNNING"
        self.store.save()
        with self.assertRaisesRegex(ValueError, "active"):
            self.store.reconcile(view["batch_id"])
        self.assertEqual(self.provider.calls, [])

    def test_thread_start_failure_leaves_no_stranded_approval(self):
        view = self.store.preview()
        with patch("pilot_v1.sg_compliance.threading.Thread.start", side_effect=RuntimeError("thread unavailable")):
            with self.assertRaises(RuntimeError):
                self.store.start(view["batch_id"], view["approval_hash"])
        self.assertEqual(self.store.summary()["counts"], {"FAILED": 3})
        self.assertEqual(self.provider.calls, [])
        with self.assertRaises(ValueError):
            self.store.start(view["batch_id"], view["approval_hash"])


if __name__ == "__main__":
    unittest.main()
