from datetime import datetime, timezone
import unittest

from pilot_v1.sg_compliance import ConfigComplianceReader, digest


class FakeConfig:
    def __init__(self):
        self.calls = []

    def describe_configuration_recorder_status(self):
        return {"ConfigurationRecordersStatus": [{"recording": True, "lastStatus": "SUCCESS"}]}

    def describe_config_rules(self, ConfigRuleNames):
        return {"ConfigRules": [{"ConfigRuleName": ConfigRuleNames[0]}]}

    def get_compliance_details_by_config_rule(self, **kwargs):
        self.calls.append(kwargs)
        control = kwargs["ConfigRuleName"]
        resource_type = "AWS::S3::Bucket" if control.startswith("s3-") else "AWS::EC2::SecurityGroup"
        start = 0 if "NextToken" not in kwargs else 100
        count = 100 if start == 0 else 5
        rows = []
        for i in range(start, start + count):
            rows.append({
                "ComplianceType": "NON_COMPLIANT" if i % 2 == 0 else "COMPLIANT",
                "ResultRecordedTime": datetime(2026, 9, 11, 7, 0, i % 60, tzinfo=timezone.utc),
                "EvaluationResultIdentifier": {"EvaluationResultQualifier": {
                    "ConfigRuleName": control, "ResourceType": resource_type, "ResourceId": f"resource-{i:03d}",
                }},
            })
        return {"EvaluationResults": rows, **({"NextToken": "next"} if start == 0 else {})}


class ConfigComplianceTests(unittest.TestCase):
    def test_summary_is_bounded_paginated_and_two_controls_only(self):
        fake = FakeConfig()
        summary = ConfigComplianceReader(fake).summary()
        self.assertEqual(summary["source"], "AWS Config")
        self.assertEqual({x["control"] for x in summary["controls"]}, {
            "s3-bucket-level-public-access-prohibited", "restricted-ssh"
        })
        self.assertTrue(all(x["total_observed"] == 105 and not x["partial"] for x in summary["controls"]))
        self.assertEqual(len(fake.calls), 4)
        self.assertEqual(fake.calls[1]["NextToken"], "next")

    def test_finding_identity_and_family_are_deterministic(self):
        reader = ConfigComplianceReader(FakeConfig())
        first = reader.list_findings("restricted-ssh", limit=5)["items"][0]
        again = reader.list_findings("restricted-ssh", limit=5)["items"][0]
        expected = digest({"source": "AWS Config", "control": "restricted-ssh",
                           "resource_type": "SECURITY_GROUP", "resource_id": first["resource_id"]})
        self.assertEqual(first["finding_id"], expected)
        self.assertEqual(first["finding_id"], again["finding_id"])
        self.assertEqual(first["remediation_family"], "SG_RESTRICTED_SSH")
        self.assertIn("cannot authorize", first["remediation_scope"])

    def test_invalid_control_and_inactive_recorder_fail_closed(self):
        reader = ConfigComplianceReader(FakeConfig())
        with self.assertRaises(ValueError):
            reader.list_findings("not-approved")

        class Inactive(FakeConfig):
            def describe_configuration_recorder_status(self):
                return {"ConfigurationRecordersStatus": [{"recording": False, "lastStatus": "SUCCESS"}]}
        with self.assertRaises(RuntimeError):
            ConfigComplianceReader(Inactive()).summary()


if __name__ == "__main__":
    unittest.main()
