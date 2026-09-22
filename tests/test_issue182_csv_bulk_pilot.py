import csv
import io
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "agents" / "compliance-agent-v1" / "src"
sys.path.insert(0, str(SRC))

from compliance_agent_v1.csv_bulk_pilot import (  # noqa: E402
    MAX_CANDIDATE_ROWS, Candidate, CsvCandidatePilot, NoopExecutor, parse_candidate_csv,
)
from compliance_agent_v1.scaled_findings import ScaledFindingStore, generate_findings  # noqa: E402


def candidate_csv(rows):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=("account_alias", "control_key", "resource_id"), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode()


def ssh(alias, number):
    return {
        "account_alias": alias,
        "control_key": "restricted_ssh",
        "resource_id": f"sg-{alias}-ssh-{number:02d}",
    }


class CsvCandidatePilotTests(unittest.TestCase):
    def mixed_pilot(self):
        rows = [dict(row) for row in generate_findings()]
        next(row for row in rows if row["resource_id"] == "sg-lab-002-ssh-01")["config_status"] = "COMPLIANT"
        pilot = CsvCandidatePilot(ScaledFindingStore(rows))
        content = candidate_csv([
            ssh("lab-001", 1), ssh("lab-001", 1), ssh("lab-002", 1),
            {"account_alias": "lab-999", "control_key": "restricted_ssh", "resource_id": "sg-lab-999-ssh-01"},
            {"account_alias": "lab-003", "control_key": "s3_ssl", "resource_id": "bucket-lab-003-ssl-01"},
            ssh("lab-004", 5),
        ])
        return pilot, content

    def test_strict_intake_is_bounded_and_never_interprets_csv_as_instructions(self):
        self.assertEqual(parse_candidate_csv(candidate_csv([ssh("lab-001", 1)])), (Candidate(**ssh("lab-001", 1)),))
        bad = (
            b"account_alias,control_key\nlab-001,restricted_ssh\n",
            b"account_alias,control_key,resource_id,private\nlab-001,restricted_ssh,sg-lab-001-ssh-01,no\n",
            b"account_alias,control_key,resource_id\n=instruction,restricted_ssh,sg-lab-001-ssh-01\n",
            b"account_alias,control_key,resource_id\nlab-001,restricted_ssh,\n",
        )
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_candidate_csv(value)
        too_many = candidate_csv([ssh("lab-001", 1)] * (MAX_CANDIDATE_ROWS + 1))
        with self.assertRaisesRegex(ValueError, "row limit"):
            parse_candidate_csv(too_many)

    def test_backend_reresolve_classifies_mixed_candidates_and_bounds_model_view(self):
        pilot, content = self.mixed_pilot()
        preview = pilot.preview(content)
        self.assertEqual(
            {key: preview[key] for key in ("submitted", "normalized", "duplicates", "eligible", "rejected", "excluded")},
            {"submitted": 6, "normalized": 5, "duplicates": 1, "eligible": 1, "rejected": 4, "excluded": 1},
        )
        states = {row["preview_state"] for row in pilot._batches[preview["batch_id"]]["rows"]}
        self.assertEqual(states, {"ELIGIBLE", "DUPLICATE", "STALE", "UNKNOWN", "UNSUPPORTED", "EXCLUDED"})
        self.assertEqual(preview["control"], "restricted_ssh")
        self.assertEqual(preview["account_count"], 1)
        self.assertTrue(preview["zero_writes"])
        self.assertEqual(preview["model_context"], "COMPACT_SUMMARY_AND_BOUNDED_REJECTIONS")
        self.assertLess(len(json.dumps(preview)), 20_000)

    def test_all_rejected_preview_never_creates_an_empty_frozen_batch(self):
        pilot = CsvCandidatePilot()
        preview = pilot.preview(candidate_csv([ssh("lab-001", 5)]))
        self.assertEqual(preview["freeze_state"], "NO_ELIGIBLE_CANDIDATES")
        self.assertIsNone(preview["batch_id"])
        self.assertEqual(pilot._batches, {})

    def test_freeze_is_canonical_and_evidence_or_csv_changes_require_prepare(self):
        pilot = CsvCandidatePilot()
        first = pilot.preview(candidate_csv([ssh("lab-003", 1), ssh("lab-001", 1)]))
        reordered = pilot.preview(candidate_csv([ssh("lab-001", 1), ssh("lab-003", 1)]))
        self.assertEqual(first["scope_hash"], reordered["scope_hash"])
        edited = pilot.preview(candidate_csv([ssh("lab-001", 1)]))
        self.assertNotEqual(first["batch_id"], edited["batch_id"])

        changed = [dict(row) for row in generate_findings()]
        next(row for row in changed if row["resource_id"] == "sg-lab-001-ssh-01")["config_status"] = "COMPLIANT"
        pilot.store = ScaledFindingStore(changed)
        with self.assertRaisesRegex(ValueError, "re-prepare"):
            pilot.decide(first["batch_id"], first["scope_hash"], "APPROVE")

    def test_native_reject_has_zero_dispatch_and_replay_fails_closed(self):
        pilot = CsvCandidatePilot()
        preview = pilot.preview(candidate_csv([ssh("lab-001", 1)]))
        executor = NoopExecutor()
        result = pilot.decide(preview["batch_id"], preview["scope_hash"], "REJECT")
        self.assertEqual(result["decision"], "REJECTED")
        self.assertEqual(result["executor"], "NOT_DISPATCHED")
        self.assertEqual(executor.dispatched, [])
        with self.assertRaises(ValueError):
            pilot.execute_approved(preview["batch_id"], preview["scope_hash"], executor)
        with self.assertRaisesRegex(ValueError, "terminal"):
            pilot.decide(preview["batch_id"], preview["scope_hash"], "REJECT")
        fresh = pilot.preview(candidate_csv([ssh("lab-001", 1)]))
        self.assertNotEqual(fresh["batch_id"], preview["batch_id"])
        self.assertEqual(fresh["scope_hash"], preview["scope_hash"])

    def test_native_approve_dispatches_only_exact_eligible_set_and_exports_all_results(self):
        pilot, content = self.mixed_pilot()
        preview = pilot.preview(content)
        pilot.decide(preview["batch_id"], preview["scope_hash"], "APPROVE")
        executor = NoopExecutor()
        result = pilot.execute_approved(preview["batch_id"], preview["scope_hash"], executor)
        self.assertEqual(executor.dispatched, ["f-lab-001-restricted_ssh-01"])
        self.assertEqual(
            {key: result[key] for key in ("decision", "approved", "attempted", "succeeded", "failed", "aws_mutation")},
            {"decision": "COMPLETED", "approved": 1, "attempted": 1, "succeeded": 1, "failed": 0, "aws_mutation": False},
        )
        rows = list(csv.DictReader(io.StringIO(pilot.result_csv(preview["batch_id"], preview["scope_hash"]))))
        self.assertEqual(len(rows), 6)
        self.assertEqual(sum(row["execution_state"] == "NOOP_SUCCEEDED" for row in rows), 1)
        self.assertEqual(sum(row["execution_state"] == "NOT_DISPATCHED" for row in rows), 5)
        receipt = pilot.result_export_receipt(preview["batch_id"], preview["scope_hash"])
        self.assertEqual(receipt["row_count"], 6)
        self.assertFalse(receipt["content_in_model_context"])
        self.assertNotIn("content", receipt)
        with self.assertRaisesRegex(ValueError, "terminal"):
            pilot.execute_approved(preview["batch_id"], preview["scope_hash"], executor)

    def test_partial_noop_failure_is_explicit_and_never_retried(self):
        pilot = CsvCandidatePilot()
        preview = pilot.preview(candidate_csv([ssh("lab-001", 1), ssh("lab-001", 2)]))
        pilot.decide(preview["batch_id"], preview["scope_hash"], "APPROVE")
        executor = NoopExecutor({"f-lab-001-restricted_ssh-02"})
        result = pilot.execute_approved(preview["batch_id"], preview["scope_hash"], executor)
        self.assertEqual((result["decision"], result["attempted"], result["succeeded"], result["failed"]), ("PARTIAL", 2, 1, 1))
        with self.assertRaisesRegex(ValueError, "terminal"):
            pilot.execute_approved(preview["batch_id"], preview["scope_hash"], executor)


if __name__ == "__main__":
    unittest.main()
