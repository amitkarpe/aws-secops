from pathlib import Path
import csv
import io
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agents" / "compliance-agent-v1" / "src"))

from compliance_agent_v1.csv_bulk_pilot import NoopExecutor  # noqa: E402
from compliance_agent_v1.exceptions_audit import AuditLedger, ExceptionAuditPilot, ExceptionRegistry  # noqa: E402


def finding(number: int) -> str:
    return f"f-lab-001-restricted_ssh-{number:02d}"


def exception(*, created_at="2026-09-22T00:00:00Z", expires_at="2026-09-23T00:00:00Z", reason="approved maintenance"):
    return {
        "account_alias": "lab-001", "control_key": "restricted_ssh",
        "resource_id": "sg-lab-001-ssh-01", "owner": "lab-owner",
        "reason": reason, "reference": "LAB-186", "created_at": created_at,
        "expires_at": expires_at,
    }


class ExceptionsAuditTests(unittest.TestCase):
    def test_strict_append_only_exception_revisions_and_bounded_views(self):
        registry = ExceptionRegistry()
        with self.assertRaisesRegex(ValueError, "exactly"):
            registry.create({**exception(), "private": "no"})
        created = registry.create(exception())
        revised = registry.revise(created["exception_id"], exception(reason="approved extended maintenance"))
        revoked = registry.revoke(created["exception_id"])
        self.assertEqual((created["revision"], revised["revision"], revoked["revision"], revoked["status"]), (1, 2, 3, "REVOKED"))
        self.assertEqual(registry.summary(), {"version": 1, "total": 1, "active": 0, "expiring_soon": 0, "expired": 0, "revoked": 1, "read_only": True})
        page = registry.page(limit=1)
        self.assertEqual((page["total_count"], len(page["items"]), page["model_context"]), (1, 1, "ONE_BOUNDED_EXCEPTION_PAGE"))
        exported = list(csv.DictReader(io.StringIO(registry.export_csv())))
        self.assertEqual((len(exported), exported[0]["status"]), (1, "REVOKED"))

    def test_active_expired_and_revoked_are_exact_and_never_compliance(self):
        active = ExceptionAuditPilot()
        record = active.add_exception(exception())
        active.add(finding(1))
        active.add(finding(2))
        preview = active.preview_selection()
        rows = active._batches[preview["batch_id"]]["rows"]
        self.assertEqual([(row["finding_id"], row["preview_state"]) for row in rows], [(finding(1), "EXCLUDED"), (finding(2), "ELIGIBLE")])
        self.assertEqual((preview["excluded"], preview["eligible"]), (1, 1))
        self.assertNotIn("COMPLIANT", str(rows))

        expired = ExceptionAuditPilot()
        expired.add_exception(exception(created_at="2026-09-21T00:00:00Z", expires_at="2026-09-22T00:00:00Z"))
        expired.add(finding(1))
        self.assertEqual(expired.preview_selection()["eligible"], 1)

        active.revoke_exception(record["exception_id"])
        renewed = active.preview_selection()
        self.assertEqual(renewed["eligible"], 2)

    def test_exception_state_is_frozen_and_changed_state_requires_reprepare(self):
        pilot = ExceptionAuditPilot()
        pilot.add(finding(1))
        first = pilot.preview_selection()
        pilot.add_exception(exception())
        with self.assertRaisesRegex(ValueError, "exception state changed; re-prepare"):
            pilot.decide(first["batch_id"], first["scope_hash"], "APPROVE")
        second = pilot.preview_selection()
        self.assertNotEqual(first["scope_hash"], second["scope_hash"])
        self.assertEqual(second["freeze_state"], "NO_ELIGIBLE_CANDIDATES")
        self.assertIn("DECISION_BLOCKED", [event["event_type"] for event in pilot.ledger.page(limit=100)["items"]])

    def test_conflicting_active_records_fail_and_stale_target_is_explicit(self):
        pilot = ExceptionAuditPilot()
        pilot.add_exception(exception())
        pilot.add_exception(exception(reason="second conflicting maintenance"))
        pilot.add(finding(1))
        with self.assertRaisesRegex(ValueError, "conflicting"):
            pilot.preview_selection()

        stale = ExceptionAuditPilot()
        payload = exception()
        payload["resource_id"] = "sg-lab-001-ssh-99"
        stale.add_exception(payload)
        self.assertEqual(stale.exception_view(limit=1)["page"]["items"][0]["target_state"], "STALE_TARGET")

    def test_reject_approve_partial_replay_and_distinct_verification_are_audited(self):
        rejected = ExceptionAuditPilot()
        rejected.add(finding(2))
        preview = rejected.preview_selection()
        result = rejected.decide(preview["batch_id"], preview["scope_hash"], "REJECT")
        self.assertEqual((result["decision"], result["attempted"], result["executor"], result["aws_mutation"]), ("REJECTED", 0, "NOT_DISPATCHED", False))
        with self.assertRaisesRegex(ValueError, "terminal"):
            rejected.decide(preview["batch_id"], preview["scope_hash"], "REJECT")
        events = rejected.ledger.timeline(preview["batch_id"])["event_types"]
        self.assertIn("NATIVE_APPROVAL_DECISION", events)
        self.assertIn("REPLAY_BLOCKED", events)
        self.assertNotIn("EXECUTION_DISPATCH", events)

        approved = ExceptionAuditPilot()
        approved.add(finding(1))
        approved.add(finding(2))
        preview = approved.preview_selection()
        approved.decide(preview["batch_id"], preview["scope_hash"], "APPROVE")
        result = approved.execute_approved(preview["batch_id"], preview["scope_hash"], NoopExecutor({finding(2)}))
        approved.record_provider_verification(preview["batch_id"], preview["scope_hash"], "READBACK_RECORDED")
        approved.record_config_convergence(preview["batch_id"], preview["scope_hash"], "PENDING")
        self.assertEqual((result["decision"], result["attempted"], result["succeeded"], result["failed"], result["aws_mutation"]), ("PARTIAL", 2, 1, 1, False))
        events = approved.ledger.timeline(preview["batch_id"])["event_types"]
        self.assertEqual(events[-4:], ["EXECUTION_DISPATCH", "EXECUTION_RESULT", "PROVIDER_VERIFICATION", "CONFIG_CONVERGENCE"])
        with self.assertRaisesRegex(ValueError, "terminal"):
            approved.execute_approved(preview["batch_id"], preview["scope_hash"])

    def test_bounded_audit_export_is_hash_chained_evidence_not_authorization(self):
        pilot = ExceptionAuditPilot()
        pilot.record_discovery_query(evidence_digest=pilot.store.evidence_receipt()["evidence_digest"])
        pilot.record_candidate_intake(candidate_digest="public-candidate-digest")
        pilot.add(finding(1))
        pilot.preview_selection()
        page = pilot.ledger.page(limit=2)
        self.assertEqual((len(page["items"]), page["model_context"], page["read_only"]), (2, "ONE_BOUNDED_AUDIT_PAGE", True))
        for prior, current in zip(page["items"], pilot.ledger.page(limit=100)["items"][1:]):
            self.assertEqual(current["prior_hash"], prior["event_hash"])
        receipt = pilot.ledger.export_receipt()
        self.assertEqual((receipt["row_count"], receipt["content_in_model_context"], receipt["read_only"]), (5, False, True))
        self.assertFalse(hasattr(pilot.ledger, "decide"))

    def test_operator_views_and_exports_are_bounded_and_backend_only(self):
        pilot = ExceptionAuditPilot()
        pilot.add_exception(exception())
        exception_view = pilot.exception_view(limit=1)
        self.assertEqual((exception_view["summary"]["active"], len(exception_view["page"]["items"]), exception_view["page"]["model_context"]), (1, 1, "ONE_BOUNDED_EXCEPTION_PAGE"))
        exception_export = pilot.exception_export_receipt()
        audit_export = pilot.audit_export_receipt()
        self.assertEqual((exception_export["filename"], exception_export["row_count"], exception_export["content_in_model_context"]), ("synthetic-exceptions.csv", 1, False))
        self.assertEqual((audit_export["filename"], audit_export["row_count"], audit_export["content_in_model_context"]), ("synthetic-audit-ledger.jsonl", 3, False))
        self.assertEqual(pilot.audit_view(limit=1)["model_context"], "ONE_BOUNDED_AUDIT_PAGE")

    def test_optional_jsonl_ledger_reopens_and_detects_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            ledger = AuditLedger(path)
            ledger.append("DISCOVERY_QUERY", outcome="RECORDED", source="test")
            self.assertEqual(AuditLedger(path).page()["total_count"], 1)
            path.write_text('{"sequence":1}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "integrity"):
                AuditLedger(path)


if __name__ == "__main__":
    unittest.main()
