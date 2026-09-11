import tempfile
import time
from pathlib import Path
import unittest

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


if __name__ == "__main__":
    unittest.main()
