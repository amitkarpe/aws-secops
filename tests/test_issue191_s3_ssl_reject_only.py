import unittest

from pilot_v1.s3_ssl_reject_only import S3SslRejectOnlyDecision


def evidence():
    return {"control": "s3_ssl", "read_only": True, "evidence_digest": "a" * 64, "accounts": [
        {"alias": "lab-dev", "identity_verified": True, "state": "AVAILABLE", "statuses": [
            {"resource_ref": "bucket-ref-123", "status": "NON_COMPLIANT"}
        ]}
    ]}


class S3SslRejectOnlyTests(unittest.TestCase):
    def test_reject_is_exact_terminal_zero_dispatch_and_write(self):
        value = S3SslRejectOnlyDecision(evidence())
        batch = value.prepare(alias="lab-dev")
        self.assertEqual(value.decide(**batch, decision="reject"), {"decision": "REJECTED", "remediation_dispatches": 0, "aws_writes": 0})
        self.assertEqual([event["event"] for event in value.events], ["PREPARE_FROZEN", "NATIVE_APPROVAL_DECISION"])


    def test_approve_is_blocked_before_any_executor_or_write(self):
        value = S3SslRejectOnlyDecision(evidence())
        batch = value.prepare(alias="lab-dev")
        self.assertEqual(value.decide(**batch, decision="approve"), {"decision": "LIVE_EXECUTION_NOT_AUTHORIZED", "remediation_dispatches": 0, "aws_writes": 0})


    def test_mismatched_scope_is_denied(self):
        value = S3SslRejectOnlyDecision(evidence())
        batch = value.prepare(alias="lab-dev")
        with self.assertRaisesRegex(ValueError, "does not match"):
            value.decide(batch_id=batch["batch_id"], scope_hash="0" * 24, decision="reject")
