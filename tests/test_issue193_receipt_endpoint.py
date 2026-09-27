"""Loopback HTTP contract for the final-decision receipt endpoint."""
from http.server import HTTPServer
from pathlib import Path
from threading import Thread
from unittest.mock import patch
import hashlib
import hmac
import http.client
import json
import tempfile
import time
import unittest

from pilot_v1.native_decision_receipt import CONTROL, TOOL, NativeDecisionReceipts
from pilot_v1.operator_server import OperatorHandler


class ReceiptEndpointTests(unittest.TestCase):
    def test_signed_reject_and_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            store = NativeDecisionReceipts(Path(directory) / "receipts.sqlite3")
            binding = dict(tool=TOOL, control=CONTROL, batch_id="a" * 20,
                           scope_hash="b" * 24, user_id="native-user-123")
            store.register(**binding, expires_at=int(time.time()) + 120)

            class Service:
                def native_decision_receipts(self):
                    return store

                def record_s3_ssl_native_decision(self, **receipt):
                    result = store.record(**receipt)
                    result["provider_readback"] = "UNCHANGED" if receipt["decision"] == "reject" else "NOT_REQUIRED"
                    if receipt["decision"] == "reject":
                        store.append_evidence(batch_id=receipt["batch_id"], scope_hash=receipt["scope_hash"],
                                              event_type="POST_REJECT_READBACK", outcome="UNCHANGED",
                                              detail_hash="c" * 64)
                    result["audit"] = store.timeline(receipt["batch_id"])
                    return result

            class Handler(OperatorHandler):
                service = Service()

                def log_message(self, *_args):
                    pass

            server = HTTPServer(("127.0.0.1", 0), Handler)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
            body = json.dumps({**binding, "action_id": "action-12345678",
                               "generation_id": "1790000000000", "decision": "reject",
                               "decided_at": int(time.time())}).encode()
            secret = "test-only-receipt-key-over-thirty-two-bytes"
            signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

            def post(sig):
                connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=2)
                connection.request("POST", "/api/operator/native-decision-receipt", body,
                                   {"Host": f"127.0.0.1:{server.server_port}",
                                    "Origin": f"http://127.0.0.1:{server.server_port}",
                                    "Content-Type": "application/json",
                                    "X-SecOps-Decision-Signature": sig})
                response = connection.getresponse()
                result = response.status, json.loads(response.read())
                connection.close()
                return result

            with patch.dict("os.environ", {"SECOPS_DECISION_RECEIPT_SECRET": secret}):
                self.assertEqual(post("wrong")[0], 403)
                status, result = post(signature)
                self.assertEqual(status, 200)
                self.assertEqual((result["outcome"], result["downstream_dispatches"], result["provider_readback"]),
                                 ("REJECTED", 0, "UNCHANGED"))
                self.assertEqual(post(signature)[0], 400)
            self.assertEqual([item["event"] for item in NativeDecisionReceipts(store.path).timeline(binding["batch_id"])],
                             ["PREPARE_FROZEN", "NATIVE_APPROVAL_DECISION", "POST_REJECT_READBACK"])
