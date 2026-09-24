from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest

from pilot_v1.native_decision_receipt import (
    CONTROL, TOOL, NativeDecisionReceipts, ReceiptError,
)


class NativeDecisionReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "receipts.sqlite3"
        self.store = NativeDecisionReceipts(self.path)
        self.binding = dict(tool=TOOL, control=CONTROL, batch_id="a" * 20,
                            scope_hash="b" * 24, user_id="native-user-123")
        self.store.register(**self.binding, expires_at=int(time.time()) + 120)

    def decide(self, store=None, **changes):
        payload = {**self.binding, "action_id": "action-12345678",
                   "generation_id": "1790000000000", "decision": "reject",
                   "decided_at": int(time.time()), **changes}
        return (store or self.store).record(**payload)

    def test_reject_exact_once_and_reopen(self):
        result = self.decide()
        self.assertEqual((result["outcome"], result["downstream_dispatches"], result["aws_writes"]), ("REJECTED", 0, 0))
        reopened = NativeDecisionReceipts(self.path)
        self.assertEqual(len(reopened.timeline(self.binding["batch_id"])), 2)
        with self.assertRaisesRegex(ReceiptError, "consumed"):
            self.decide(reopened)

    def test_approve_is_durably_blocked(self):
        result = self.decide(decision="approve")
        self.assertEqual((result["outcome"], result["live_execution_authorized"], result["downstream_dispatches"], result["aws_writes"]), ("APPROVE_BLOCKED", False, 0, 0))
        timeline = NativeDecisionReceipts(self.path).timeline(self.binding["batch_id"])
        self.assertEqual(timeline[-1]["outcome"], "APPROVE_BLOCKED")

    def test_racing_submits_have_one_winner(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self._try_decide(), range(2)))
        self.assertEqual(sorted(results), ["REJECTED", "REJECTED_BY_STORE"])
        self.assertEqual(len(self.store.timeline(self.binding["batch_id"])), 2)

    def _try_decide(self):
        try:
            return self.decide()["outcome"]
        except ReceiptError:
            return "REJECTED_BY_STORE"

    def test_wrong_tool_control_batch_scope_user_action_and_generation_fail(self):
        for changes in ({"tool": "execute_multi_account_remediation"}, {"control": "restricted-ssh"},
                        {"batch_id": "c" * 20}, {"scope_hash": "c" * 24},
                        {"user_id": "wrong-user-12345"}, {"action_id": "bad"},
                        {"generation_id": "bad"}):
            with self.subTest(changes=changes), self.assertRaises(ReceiptError):
                self.decide(**changes)
        self.assertEqual([row["event"] for row in self.store.timeline(self.binding["batch_id"])], ["PREPARE_FROZEN"])

    def test_stale_timestamp_and_expired_batch_fail(self):
        with self.assertRaisesRegex(ReceiptError, "stale"):
            self.decide(decided_at=int(time.time()) - 61)
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE frozen SET expires_at=0 WHERE batch_id=?", (self.binding["batch_id"],))
        with self.assertRaisesRegex(ReceiptError, "stale"):
            self.decide()

    def test_write_failure_does_not_consume_batch(self):
        original = self.store._connect
        self.store._connect = lambda: (_ for _ in ()).throw(OSError("disk unavailable"))
        with self.assertRaises(OSError):
            self.decide()
        self.store._connect = original
        self.assertEqual([row["event"] for row in self.store.timeline(self.binding["batch_id"])], ["PREPARE_FROZEN"])

    def test_tamper_is_detected_after_reopen(self):
        self.decide()
        with sqlite3.connect(self.path) as db:
            db.execute("DROP TRIGGER receipt_no_update")
            db.execute("UPDATE receipt SET outcome='REJECTED_CHANGED'")
        with self.assertRaisesRegex(ReceiptError, "integrity"):
            NativeDecisionReceipts(self.path)
