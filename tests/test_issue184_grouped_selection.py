import csv
import io
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "agents" / "compliance-agent-v1" / "src"
sys.path.insert(0, str(SRC))

from compliance_agent_v1.csv_bulk_pilot import NoopExecutor  # noqa: E402
from compliance_agent_v1.grouped_selection_pilot import GroupedSelectionPilot  # noqa: E402
from compliance_agent_v1.scaled_findings import ScaledFindingStore, generate_findings  # noqa: E402


def finding(alias, number):
    return f"f-{alias}-restricted_ssh-{number:02d}"


class GroupedManualSelectionTests(unittest.TestCase):
    def changed_store(self, target_finding_id, **changes):
        rows = [dict(row) for row in generate_findings()]
        next(row for row in rows if row["finding_id"] == target_finding_id).update(changes)
        return ScaledFindingStore(rows)

    def test_grouped_pages_are_bounded_and_never_change_explicit_selection(self):
        pilot = GroupedSelectionPilot()
        first = pilot.view(exception_status="NONE", page=1, limit=10, group_by="account_alias")
        self.assertEqual((first["page"]["total_count"], first["page"]["returned_count"]), (200, 10))
        self.assertEqual(len(first["groups"]["groups"]), 50)
        self.assertEqual({group["count"] for group in first["groups"]["groups"]}, {4})
        pilot.add(finding("lab-001", 1))
        second = pilot.view(exception_status="NONE", page=2, limit=10, sort_by="resource_id", sort_direction="desc", group_by="control_key")
        self.assertEqual(second["selection"]["selected_count"], 1)
        self.assertNotIn("finding_ids", second["selection"])
        self.assertEqual(second["groups"]["groups"], [{"key": "restricted_ssh", "count": 200}])
        self.assertEqual(second["model_context"], "ONE_BOUNDED_PAGE_AND_GROUP_COUNTS")

    def test_only_exact_current_ids_can_be_added_and_removed(self):
        pilot = GroupedSelectionPilot()
        receipt = pilot.add(finding("lab-001", 1))
        self.assertEqual(receipt["selected_count"], 1)
        self.assertEqual(pilot.remove(finding("lab-001", 1))["selected_count"], 0)
        with self.assertRaisesRegex(ValueError, "unknown"):
            pilot.add("private-id")
        with self.assertRaisesRegex(ValueError, "unsupported"):
            pilot.add("f-lab-001-s3_ssl-01")
        stale = GroupedSelectionPilot(self.changed_store(finding("lab-001", 1), config_status="COMPLIANT"))
        with self.assertRaisesRegex(ValueError, "stale"):
            stale.add(finding("lab-001", 1))

    def test_filtered_select_all_materializes_only_current_filtered_server_set(self):
        pilot = GroupedSelectionPilot()
        selected = pilot.select_all_current_filter(account_alias="lab-001", exception_status="NONE")
        self.assertEqual(selected["selected_count"], 4)
        self.assertEqual(sorted(pilot._selection), [finding("lab-001", number) for number in range(1, 5)])
        before = dict(selected)
        pilot.view(account_alias="lab-002", exception_status="NONE", page=1, sort_by="resource_id", sort_direction="desc")
        self.assertEqual(pilot.selection_receipt(), before)
        self.assertNotIn(finding("lab-002", 1), pilot._selection)

    def test_preview_reresolves_and_freezes_only_eligible_selection(self):
        pilot = GroupedSelectionPilot()
        pilot.add(finding("lab-001", 1))
        pilot.add(finding("lab-001", 5))
        preview = pilot.preview_selection()
        self.assertEqual(
            {key: preview[key] for key in ("selected_count", "eligible", "excluded", "rejected", "account_count", "freeze_state")},
            {"selected_count": 2, "eligible": 1, "excluded": 1, "rejected": 0, "account_count": 1, "freeze_state": "FROZEN"},
        )
        self.assertIsNotNone(preview["selection_digest"])
        self.assertIsNone(preview["candidate_digest"])

        pilot.decide(preview["batch_id"], preview["scope_hash"], "APPROVE")
        executor = NoopExecutor()
        result = pilot.execute_approved(preview["batch_id"], preview["scope_hash"], executor)
        self.assertEqual(executor.dispatched, [finding("lab-001", 1)])
        self.assertEqual((result["attempted"], result["succeeded"], result["aws_mutation"]), (1, 1, False))
        exported = list(csv.DictReader(io.StringIO(pilot.result_csv(preview["batch_id"], preview["scope_hash"]))))
        self.assertEqual(len(exported), 2)
        self.assertEqual(sum(row["execution_state"] == "NOOP_SUCCEEDED" for row in exported), 1)

    def test_stale_unknown_unsupported_and_reject_fail_closed(self):
        for change, expected in (
            ({"config_status": "COMPLIANT"}, "STALE"),
            ({"control_key": "s3_ssl"}, "UNSUPPORTED"),
        ):
            with self.subTest(expected=expected):
                pilot = GroupedSelectionPilot()
                pilot.add(finding("lab-001", 1))
                pilot.store = self.changed_store(finding("lab-001", 1), **change)
                preview = pilot.preview_selection()
                self.assertEqual(preview["freeze_state"], "NO_ELIGIBLE_CANDIDATES")
                self.assertEqual(preview["rejected_page"][0]["preview_state"], expected)

        unknown = GroupedSelectionPilot()
        unknown.add(finding("lab-001", 1))
        unknown.store = self.changed_store(finding("lab-001", 1), finding_id="f-lab-001-restricted_ssh-replaced")
        preview = unknown.preview_selection()
        self.assertEqual(preview["freeze_state"], "NO_ELIGIBLE_CANDIDATES")
        self.assertEqual(preview["rejected_page"][0]["preview_state"], "UNKNOWN")

        pilot = GroupedSelectionPilot()
        pilot.add(finding("lab-001", 1))
        preview = pilot.preview_selection()
        executor = NoopExecutor()
        rejected = pilot.decide(preview["batch_id"], preview["scope_hash"], "REJECT")
        self.assertEqual((rejected["decision"], rejected["attempted"], rejected["executor"]), ("REJECTED", 0, "NOT_DISPATCHED"))
        self.assertEqual(executor.dispatched, [])
        with self.assertRaisesRegex(ValueError, "terminal"):
            pilot.decide(preview["batch_id"], preview["scope_hash"], "REJECT")

    def test_changed_evidence_requires_reprepare(self):
        pilot = GroupedSelectionPilot()
        pilot.select_all_current_filter(account_alias="lab-001", exception_status="NONE")
        preview = pilot.preview_selection()
        pilot.store = self.changed_store(finding("lab-001", 1), config_status="COMPLIANT")
        with self.assertRaisesRegex(ValueError, "re-prepare"):
            pilot.decide(preview["batch_id"], preview["scope_hash"], "APPROVE")


if __name__ == "__main__":
    unittest.main()
