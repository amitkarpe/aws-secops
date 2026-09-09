import unittest
from pathlib import Path

from pilot_v1.findings import import_findings, normalize_s3, normalize_sg, validate_finding


ROOT = Path(__file__).resolve().parents[1]
WHEN = "2026-09-10T00:00:00+00:00"


class FindingContractTest(unittest.TestCase):
    def test_existing_sg_and_s3_provider_results_map_to_common_contract(self):
        sg = normalize_sg(
            {
                "resource_id": "sg-demo",
                "resource_name": "pilot-demo",
                "control": "TCP/22",
                "status": "NON_COMPLIANT",
                "source": "0.0.0.0/0",
                "recommendation": "Remove exact rule.",
            },
            observed_at=WHEN,
        )
        self.assertEqual((sg["resource_type"], sg["severity"]), ("SECURITY_GROUP", "HIGH"))

        s3 = normalize_s3(
            {
                "resource_id": "bucket-demo",
                "resource_name": "bucket-demo",
                "recommendation": "Review failed controls.",
                "controls": [
                    {"name": name, "status": "PASS", "evidence": "provider pass"}
                    for name in (
                        "Block Public Access",
                        "Default encryption",
                        "Versioning",
                        "TLS-only bucket policy",
                        "Object ownership",
                    )
                ],
            },
            observed_at=WHEN,
        )
        self.assertEqual(len(s3), 5)
        self.assertTrue(all(item["status"] == "COMPLIANT" for item in s3))

    def test_bounded_sanitized_json_and_csv_samples_are_accepted(self):
        self.assertEqual(len(import_findings(ROOT / "examples/findings-sanitized.json")), 1)
        csv_finding = import_findings(ROOT / "examples/findings-sanitized.csv")[0]
        self.assertEqual(csv_finding["owner"], "platform-team")

    def test_invalid_or_unbounded_findings_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "severity"):
            validate_finding(
                {
                    "source": "sample",
                    "resource_type": "OTHER",
                    "resource_id": "item",
                    "resource_name": "item",
                    "environment": "demo",
                    "control": "control",
                    "severity": "URGENT",
                    "status": "NON_COMPLIANT",
                    "evidence": "sample",
                    "recommendation": "review",
                    "observed_at": WHEN,
                }
            )
        with self.assertRaisesRegex(ValueError, "between 1 and 100"):
            import_findings(ROOT / "examples/findings-sanitized.json", limit=0)


if __name__ == "__main__":
    unittest.main()
