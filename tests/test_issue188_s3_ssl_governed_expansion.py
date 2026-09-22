from pathlib import Path
import csv
import io
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agents" / "compliance-agent-v1" / "src"))

from compliance_agent_v1.capability_adapter import capability_decision  # noqa: E402
from compliance_agent_v1.csv_bulk_pilot import CsvCandidatePilot, NoopExecutor  # noqa: E402
from compliance_agent_v1.exceptions_audit import ExceptionAuditPilot  # noqa: E402


def finding(control: str, number: int) -> str:
    return f"f-lab-001-{control}-{number:02d}"


def s3_exception():
    return {
        "account_alias": "lab-001", "control_key": "s3_ssl",
        "resource_id": "bucket-lab-001-ssl-01", "owner": "lab-owner",
        "reason": "synthetic certificate maintenance", "reference": "LAB-188",
        "created_at": "2026-09-22T00:00:00Z", "expires_at": "2026-09-23T00:00:00Z",
    }


class S3SslGovernedExpansionTests(unittest.TestCase):
    def test_s3_capability_is_explicit_governed_metadata_not_authority(self):
        decision = capability_decision("s3_ssl", "REMEDIATE")
        self.assertEqual(
            {key: decision[key] for key in ("supported", "route", "requires_human_approval", "execution_authorized")},
            {"supported": True, "route": "synthetic-governed-path", "requires_human_approval": True, "execution_authorized": False},
        )
        self.assertFalse(capability_decision("s3_logging", "REMEDIATE")["supported"])

    def test_cross_control_add_and_mixed_selection_fail_closed(self):
        s3 = ExceptionAuditPilot(control="s3_ssl")
        ssh = ExceptionAuditPilot(control="restricted_ssh")
        with self.assertRaisesRegex(ValueError, "unsupported finding control"):
            s3.add(finding("restricted_ssh", 1))
        with self.assertRaisesRegex(ValueError, "unsupported finding control"):
            ssh.add(finding("s3_ssl", 1))
        s3.add(finding("s3_ssl", 1))
        s3._selection[finding("restricted_ssh", 1)] = s3.store.resolve_finding_id(finding("restricted_ssh", 1))
        preview = s3.preview_selection()
        self.assertEqual((preview["eligible"], preview["rejected"], preview["freeze_state"]), (0, 2, "NO_ELIGIBLE_CANDIDATES"))
        self.assertEqual({row["preview_state"] for row in preview["rejected_page"]}, {"UNSUPPORTED"})

        csv_pilot = CsvCandidatePilot(control="s3_ssl")
        content = (
            "account_alias,control_key,resource_id\n"
            "lab-001,s3_ssl,bucket-lab-001-ssl-01\n"
            "lab-001,restricted_ssh,sg-lab-001-ssh-01\n"
        ).encode()
        csv_preview = csv_pilot.preview(content)
        self.assertEqual((csv_preview["eligible"], csv_preview["freeze_state"]), (0, "NO_ELIGIBLE_CANDIDATES"))

    def test_control_bound_exception_excludes_only_s3_and_changes_scope(self):
        s3 = ExceptionAuditPilot(control="s3_ssl")
        ssh = ExceptionAuditPilot(control="restricted_ssh", registry=s3.registry)
        s3.add_exception(s3_exception())
        s3.add(finding("s3_ssl", 1))
        s3_preview = s3.preview_selection()
        self.assertEqual((s3_preview["eligible"], s3_preview["excluded"]), (0, 1))
        ssh.add(finding("restricted_ssh", 1))
        ssh_preview = ssh.preview_selection()
        self.assertEqual((ssh_preview["eligible"], ssh_preview["excluded"]), (1, 0))

        clean = ExceptionAuditPilot(control="s3_ssl")
        clean.add(finding("s3_ssl", 1))
        clean_preview = clean.preview_selection()
        self.assertNotEqual(clean_preview["scope_hash"], s3_preview["scope_hash"])

    def test_reject_approve_exact_rows_and_compact_audit_export(self):
        rejected = ExceptionAuditPilot(control="s3_ssl")
        rejected.add(finding("s3_ssl", 1))
        preview = rejected.preview_selection()
        result = rejected.decide(preview["batch_id"], preview["scope_hash"], "REJECT")
        self.assertEqual((result["control"], result["decision"], result["attempted"], result["executor"], result["aws_mutation"]), ("s3_ssl", "REJECTED", 0, "NOT_DISPATCHED", False))
        self.assertNotIn("EXECUTION_DISPATCH", rejected.ledger.timeline(preview["batch_id"])["event_types"])

        approved = ExceptionAuditPilot(control="s3_ssl")
        approved.add(finding("s3_ssl", 1))
        approved.add(finding("s3_ssl", 2))
        preview = approved.preview_selection()
        approved.decide(preview["batch_id"], preview["scope_hash"], "APPROVE")
        executor = NoopExecutor()
        result = approved.execute_approved(preview["batch_id"], preview["scope_hash"], executor)
        approved.record_provider_verification(preview["batch_id"], preview["scope_hash"], "READBACK_RECORDED")
        approved.record_config_convergence(preview["batch_id"], preview["scope_hash"], "PENDING")
        self.assertEqual(executor.dispatched, [finding("s3_ssl", 1), finding("s3_ssl", 2)])
        self.assertEqual((result["control"], result["attempted"], result["succeeded"], result["aws_mutation"]), ("s3_ssl", 2, 2, False))
        exported = list(csv.DictReader(io.StringIO(approved.result_csv(preview["batch_id"], preview["scope_hash"]))))
        self.assertEqual({row["control_key"] for row in exported}, {"s3_ssl"})
        view = approved.operator_view(preview["batch_id"], preview["scope_hash"])
        self.assertEqual((view["control"], view["model_context"], view["result_export"]["content_in_model_context"], view["audit_export"]["content_in_model_context"]), ("s3_ssl", "COMPACT_TWO_CONTROL_OPERATOR_RECEIPT", False, False))


if __name__ == "__main__":
    unittest.main()
