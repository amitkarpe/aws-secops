import csv
import io
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "agents" / "compliance-agent-v1" / "src"
sys.path.insert(0, str(SRC))

from compliance_agent_v1.scaled_findings import (  # noqa: E402
    CSV_FIELDS, MAX_PAGE_SIZE, FindingQuery, ScaledFindingStore, generate_findings,
    model_read,
)


class ScaledFindingTests(unittest.TestCase):
    def setUp(self):
        self.store = ScaledFindingStore()

    def test_generator_is_exact_and_deterministic(self):
        first = generate_findings()
        self.assertEqual(first, generate_findings())
        self.assertEqual(len(first), 1000)
        self.assertEqual(len({row["finding_id"] for row in first}), 1000)
        self.assertEqual(len({row["account_alias"] for row in first}), 50)
        self.assertEqual(
            {key: sum(row["control_key"] == key for row in first) for key in {
                "s3_ssl", "s3_logging", "s3_backup", "restricted_ssh"
            }},
            {"s3_ssl": 250, "s3_logging": 250, "s3_backup": 250, "restricted_ssh": 250},
        )
        self.assertEqual(sum(row["exception_status"] != "NONE" for row in first), 200)

        spec = json.loads(
            (ROOT / "agents" / "compliance-agent-v1" / "fixtures" / "1k-fixture.json").read_text()
        )
        self.assertEqual(
            (spec["total_accounts"], spec["findings_per_account"], spec["total_findings"]),
            (50, 20, 1000),
        )
        self.assertFalse(spec["randomness"])
        self.assertEqual(spec["real_aws_accounts_required"], 0)

    def test_summary_contains_counts_not_rows(self):
        summary = self.store.summary()
        self.assertEqual((summary["total_findings"], summary["account_count"]), (1000, 50))
        self.assertEqual(set(summary["control_counts"].values()), {250})
        self.assertEqual(summary["exception_status_counts"]["ONE_TIME_TEST_EXCEPTION"], 200)
        self.assertNotIn("items", summary)

    def test_backend_evidence_receipt_and_candidate_reresolution_are_public_safe(self):
        receipt = self.store.evidence_receipt()
        resolved = self.store.resolve_candidate(
            "lab-001", "restricted_ssh", "sg-lab-001-ssh-01"
        )
        self.assertEqual(receipt["version"], 1)
        self.assertEqual(len(receipt["evidence_digest"]), 64)
        self.assertNotIn("items", receipt)
        self.assertEqual(resolved["finding_id"], "f-lab-001-restricted_ssh-01")
        self.assertIsNone(self.store.resolve_candidate("lab-001", "restricted_ssh", "unknown"))

    def test_query_filters_search_sort_and_pages_server_side(self):
        query = FindingQuery(
            control_key="s3_backup", account_alias="lab-010",
            config_status="NON_COMPLIANT", exception_status="NONE",
            search="bak", sort_by="resource_id", sort_direction="desc", page=2, limit=2,
        )
        result = self.store.query(query)
        self.assertEqual((result["total_count"], result["returned_count"]), (4, 2))
        self.assertEqual(result["page_count"], 2)
        self.assertEqual(
            [row["resource_id"] for row in result["items"]],
            ["bucket-lab-010-bak-02", "bucket-lab-010-bak-01"],
        )

    def test_page_size_cap_and_invalid_values_fail_closed(self):
        self.assertEqual(len(self.store.query(FindingQuery(limit=MAX_PAGE_SIZE))["items"]), 100)
        bad = (
            FindingQuery(limit=101), FindingQuery(limit=True), FindingQuery(page=0),
            FindingQuery(page=True), FindingQuery(control_key="unknown"),
            FindingQuery(account_alias="private"), FindingQuery(search=""),
            FindingQuery(sort_by="private_field"), FindingQuery(sort_direction="sideways"),
        )
        for query in bad:
            with self.subTest(query=query), self.assertRaises(ValueError):
                self.store.query(query)

        private = [dict(row) for row in generate_findings()]
        private[0]["account_id"] = "not-public"
        with self.assertRaisesRegex(ValueError, "private field"):
            ScaledFindingStore(private)

    def test_out_of_range_page_is_deterministic(self):
        result = self.store.query(FindingQuery(control_key="s3_ssl", page=999, limit=100))
        self.assertEqual(result["total_count"], 250)
        self.assertEqual(result["returned_count"], 0)
        self.assertEqual(result["items"], [])

    def test_csv_uses_same_filters_and_public_fixed_columns(self):
        query = FindingQuery(control_key="restricted_ssh", exception_status="NONE")
        page = self.store.query(FindingQuery(
            control_key=query.control_key, exception_status=query.exception_status, limit=100
        ))
        rows = list(csv.DictReader(io.StringIO(self.store.export_csv(query))))
        self.assertEqual(len(rows), page["total_count"])
        self.assertEqual(tuple(rows[0]), CSV_FIELDS)
        self.assertTrue(all(row["control_key"] == "restricted_ssh" for row in rows))
        forbidden = {"account_id", "role_arn", "private_catalog", "finding_id"}
        self.assertFalse(forbidden.intersection(rows[0]))

    def test_model_contract_never_returns_full_dataset_or_export(self):
        page = self.store.query(FindingQuery(limit=100))
        receipt = self.store.export_receipt()
        self.assertEqual(len(page["items"]), 100)
        self.assertEqual(page["total_count"], 1000)
        self.assertEqual(page["model_context"], "ONE_BOUNDED_PAGE")
        self.assertEqual(receipt["row_count"], 1000)
        self.assertFalse(receipt["content_in_model_context"])
        self.assertNotIn("content", receipt)
        self.assertNotIn("items", receipt)
        self.assertLess(len(json.dumps(page)), 100_000)

    def test_product_read_path_supports_summary_page_and_export_receipt(self):
        summary = model_read("summary")
        page = model_read("page", control_key="s3_backup", page=2, limit=50)
        export = model_read("export", account_alias="lab-001", limit=100)
        self.assertEqual(summary["total_findings"], 1000)
        self.assertEqual((page["total_count"], page["returned_count"]), (250, 50))
        self.assertEqual(export["row_count"], 20)
        self.assertNotIn("content", export)
        with self.assertRaises(ValueError):
            model_read("mutate")

        integration = json.loads((ROOT / "integration" / "compliance-agent-v1.json").read_text())
        self.assertIn("query_synthetic_fleet_v1_mcp_compliance_agent_v1", integration["tools"])
        self.assertIn("SYNTHETIC 1K READS", integration["instructions"])
        self.assertIn("never route to prepare or execute", integration["instructions"])


if __name__ == "__main__":
    unittest.main()
