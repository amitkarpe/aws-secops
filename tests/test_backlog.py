import unittest

from pilot_v1.backlog import FindingBacklog


def finding(**changes):
    value = {
        "source": "AWS EC2",
        "resource_type": "SECURITY_GROUP",
        "resource_id": "sg-demo",
        "resource_name": "pilot-demo",
        "environment": "dev",
        "control": "TCP/22",
        "severity": "HIGH",
        "status": "NON_COMPLIANT",
        "evidence": "provider evidence",
        "recommendation": "Remove exact rule.",
        "observed_at": "2026-09-10T00:00:00+00:00",
    }
    value.update(changes)
    return value


class BacklogTest(unittest.TestCase):
    def test_summary_is_provider_derived_and_priority_ordered(self):
        backlog = FindingBacklog(
            [
                finding(),
                finding(
                    source="VAPT",
                    resource_type="EC2_INSTANCE",
                    resource_id="host-demo",
                    resource_name="host-demo",
                    control="Supported OS",
                    severity="CRITICAL",
                    observed_at="2026-09-01T00:00:00+00:00",
                ),
                finding(
                    source="AWS S3",
                    resource_type="S3_BUCKET",
                    resource_id="bucket-demo",
                    resource_name="bucket-demo",
                    control="Versioning",
                    severity="INFO",
                    status="COMPLIANT",
                ),
            ]
        )
        result = backlog.summary()
        self.assertEqual((result["total_open"], result["high_critical"]), (2, 2))
        self.assertEqual(result["priority_findings"][0]["severity"], "CRITICAL")
        self.assertEqual(result["by_resource_type"][0], {"name": "EC2_INSTANCE", "count": 1})
        self.assertIn("CRITICAL", result["recommended_focus"])

    def test_upsert_replaces_provider_status_instead_of_double_counting(self):
        backlog = FindingBacklog([finding()])
        backlog.upsert([finding(status="COMPLIANT", severity="INFO")])
        result = backlog.summary()
        self.assertEqual(result["total_findings"], 1)
        self.assertEqual(result["total_open"], 0)


if __name__ == "__main__":
    unittest.main()
