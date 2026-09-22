from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from pilot_v1.native_decision_receipt import ReceiptError
from pilot_v1.operator_server import OperatorHandler, OperatorService
from compliance_agent_v1.live_s3_ssl import _BotoS3ReadClient, MAX_BUCKETS_PER_ACCOUNT


def evidence(*, changed=False):
    return {"version": 1, "control": "s3_ssl", "region": "ap-southeast-1",
            "evidence_digest": "d" * 64 if not changed else "e" * 64,
            "accounts": [
                {"alias": alias, "identity_verified": True, "state": "AVAILABLE",
                 "provider_evidence_digest": ("c" if alias == "lab-dev" else "f") * 64,
                 "statuses": ([{"resource_ref": "bucket-ref-abcdef123456", "status": "NON_COMPLIANT"}]
                              if alias == "lab-dev" else [{"resource_ref": f"bucket-ref-{index:012d}", "status": "COMPLIANT"}])}
                for index, alias in enumerate(("lab-dev", "lab-poc", "lab-qa", "lab-sec"), start=1)
            ],
            "read_only": True, "aws_writes": 0, "raw_identifiers_emitted": False}


class Issue191NativeIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        service = object.__new__(OperatorService)
        service.execution_state = Path(self.temp.name) / "four-account-execution-plan.json"
        service._decision_receipts = None
        service._collect_s3_ssl = lambda: evidence()
        self.service = service

    def prepared_and_registered(self):
        prepared = self.service.prepare_s3_ssl_reject_only()
        self.service.register_s3_ssl_native_decision(
            tool=prepared["next_execution"]["tool"], control=prepared["control"],
            batch_id=prepared["batch_id"], scope_hash=prepared["scope_hash"],
            user_id="authenticated-user-123")
        return prepared

    def receipt(self, prepared):
        return {"tool": prepared["next_execution"]["tool"], "control": prepared["control"],
                "batch_id": prepared["batch_id"], "scope_hash": prepared["scope_hash"],
                "action_id": "action-12345678", "generation_id": "1790000000000",
                "user_id": "authenticated-user-123", "decision": "reject",
                "decided_at": int(time.time())}

    def test_prepare_native_reject_persists_receipt_then_fresh_readback(self):
        prepared = self.prepared_and_registered()
        result = self.service.record_s3_ssl_native_decision(**self.receipt(prepared))
        self.assertEqual((result["outcome"], result["provider_readback"], result["downstream_dispatches"], result["aws_writes"]),
                         ("REJECTED", "UNCHANGED", 0, 0))
        self.assertEqual([row["event"] for row in result["audit"]],
                         ["PREPARE_FROZEN", "NATIVE_APPROVAL_DECISION", "POST_REJECT_READBACK"])
        self.service.native_decision_receipts().verify()

    def test_wrong_scope_and_replay_do_not_dispatch(self):
        prepared = self.prepared_and_registered()
        receipt = self.receipt(prepared)
        with self.assertRaises(ReceiptError):
            self.service.record_s3_ssl_native_decision(**{**receipt, "scope_hash": "0" * 24})
        result = self.service.record_s3_ssl_native_decision(**receipt)
        self.assertEqual(result["downstream_dispatches"], 0)
        with self.assertRaises(ReceiptError):
            self.service.record_s3_ssl_native_decision(**receipt)

    def test_changed_provider_readback_records_failure_without_continuation(self):
        self.service._collect_s3_ssl = lambda: evidence()
        prepared = self.service.prepare_s3_ssl_reject_only()
        self.service.register_s3_ssl_native_decision(
            tool=prepared["next_execution"]["tool"], control=prepared["control"],
            batch_id=prepared["batch_id"], scope_hash=prepared["scope_hash"],
            user_id="authenticated-user-123")
        self.service._collect_s3_ssl = lambda: evidence(changed=True)
        with self.assertRaisesRegex(RuntimeError, "did not prove unchanged"):
            self.service.record_s3_ssl_native_decision(**self.receipt(prepared))
        timeline = self.service.native_decision_receipts().timeline(prepared["batch_id"])
        self.assertEqual([row["event"] for row in timeline],
                         ["PREPARE_FROZEN", "NATIVE_APPROVAL_DECISION", "POST_REJECT_READBACK"])
        self.assertEqual(timeline[-1]["outcome"], "CHANGED")

    def test_unavailable_provider_readback_is_durable_and_fails_closed(self):
        prepared = self.prepared_and_registered()
        self.service._collect_s3_ssl = lambda: (_ for _ in ()).throw(TimeoutError("provider read timed out"))
        with self.assertRaisesRegex(RuntimeError, "did not prove unchanged"):
            self.service.record_s3_ssl_native_decision(**self.receipt(prepared))
        timeline = self.service.native_decision_receipts().timeline(prepared["batch_id"])
        self.assertEqual([row["event"] for row in timeline],
                         ["PREPARE_FROZEN", "NATIVE_APPROVAL_DECISION", "POST_REJECT_READBACK"])
        self.assertEqual(timeline[-1]["outcome"], "UNAVAILABLE")

    def test_expired_exact_freeze_cannot_register_or_record(self):
        prepared = self.service.prepare_s3_ssl_reject_only()
        state = self.service._read_s3_ssl_state()
        state["expires_at"] = int(time.time()) - 1
        self.service._save_s3_ssl_state(state)
        with self.assertRaisesRegex(ValueError, "expired"):
            self.service.register_s3_ssl_native_decision(
                tool=prepared["next_execution"]["tool"], control=prepared["control"],
                batch_id=prepared["batch_id"], scope_hash=prepared["scope_hash"],
                user_id="authenticated-user-123")
        with self.assertRaisesRegex(ValueError, "expired"):
            self.service.record_s3_ssl_native_decision(**self.receipt(prepared))

    def test_s3_list_buckets_is_single_read_compatible_with_old_botocore(self):
        class S3WithoutPaginator:
            def __init__(self):
                self.calls = 0

            def list_buckets(self):
                self.calls += 1
                return {"Buckets": [{"Name": f"bucket-{index:02d}"} for index in reversed(range(25))]}

        class Session:
            def __init__(self):
                self.s3 = S3WithoutPaginator()

            def client(self, service, region_name=None):
                return self.s3 if service == "s3" else object()

        session = Session()
        names = _BotoS3ReadClient(session).list_bucket_names()
        self.assertEqual(session.s3.calls, 1)
        self.assertEqual(len(names), MAX_BUCKETS_PER_ACCOUNT)
        self.assertEqual(names, [f"bucket-{index:02d}" for index in range(MAX_BUCKETS_PER_ACCOUNT)])

    def test_runtime_deploy_binds_management_profile_and_rollback_removes_only_issue191_dropins(self):
        deploy = (Path(__file__).resolve().parents[1] / "scripts" / "issue191-deploy-runtime.sh").read_text()
        rollback = (Path(__file__).resolve().parents[1] / "scripts" / "issue191-rollback-runtime.sh").read_text()
        self.assertIn("install_dropin \"$bulk_dropin\" yes", deploy)
        self.assertIn("Environment=SECOPS_LAB_PROFILE=amit", deploy)
        self.assertIn("grep -Fxq 'SECOPS_LAB_PROFILE=amit'", deploy)
        self.assertIn('systemctl restart aws-secops-bulk.service', deploy)
        self.assertLess(deploy.index("ss -ltnH 'sport = :4444' | grep -q ."),
                        deploy.index("http://127.0.0.1:4444/api/operator/s3-ssl-status"))
        self.assertIn('rm -f /etc/systemd/system/aws-secops-bulk.service.d/issue191.conf', rollback)
        self.assertIn('systemctl start aws-secops-bulk.service', rollback)

    def test_live_status_failure_response_and_log_do_not_expose_exception_message(self):
        private_message = "private account-specific failure detail"

        class Service:
            @staticmethod
            def s3_ssl_live_status():
                raise ModuleNotFoundError(private_message, name="compliance_agent_v1")

        class Handler:
            path = "/api/operator/s3-ssl-status"
            service = Service()
            response = None

            @staticmethod
            def _local_host():
                return True

            def _json(self, status, body):
                self.response = (status, body)

        handler = Handler()
        with patch("pilot_v1.operator_server.logging.getLogger") as get_logger:
            logger = get_logger.return_value
            OperatorHandler.do_GET(handler)
        self.assertEqual(handler.response, (503, {"error": "live s3_ssl read unavailable"}))
        logger.warning.assert_called_once_with(
            "s3_ssl live read unavailable (%s, module=%s)",
            "ModuleNotFoundError", "compliance_agent_v1",
        )
        self.assertNotIn(private_message, str(handler.response))


if __name__ == "__main__":
    unittest.main()
