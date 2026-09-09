import csv
import io
import unittest

from pilot_v1.export import to_csv, to_markdown


class ExportTest(unittest.TestCase):
    def test_csv_and_markdown_use_same_open_finding(self):
        findings = [
            {
                "source": "AWS S3",
                "resource_type": "S3_BUCKET",
                "resource_id": "bucket-demo",
                "resource_name": "archive-demo",
                "environment": "dev",
                "control": "Versioning",
                "severity": "MEDIUM",
                "status": "NON_COMPLIANT",
                "evidence": "not enabled",
                "recommendation": "Enable after approval.",
                "observed_at": "2026-09-10T00:00:00+00:00",
                "owner": "=untrusted-formula",
                "target": "2026-Q4",
            }
        ]
        csv_rows = list(csv.DictReader(io.StringIO(to_csv(findings))))
        self.assertEqual(csv_rows[0]["finding"], "S3_BUCKET/archive-demo: Versioning")
        self.assertEqual(csv_rows[0]["approval_required"], "YES")
        self.assertEqual(csv_rows[0]["owner"], "'=untrusted-formula")
        markdown = to_markdown(findings)
        self.assertIn("Open actions: **1**", markdown)
        self.assertIn("=untrusted-formula", markdown)
        self.assertIn("2026-Q4", markdown)


if __name__ == "__main__":
    unittest.main()
