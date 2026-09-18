import json
import unittest

from pilot_v1.org_config_overview import (
    ALIASES,
    S3_CONTROL,
    SG_CONTROL,
    parse_targets,
    read_status,
    remediation_plan,
)


RAW = json.dumps([
    {"alias": "lab-dev", "account_id": "111111111111"},
    {"alias": "lab-poc", "account_id": "222222222222"},
    {"alias": "lab-qa", "account_id": "333333333333"},
    {"alias": "lab-sec", "account_id": "444444444444"},
])


def aggregate():
    return {
        "AggregateComplianceByConfigRules": [
            {
                "AccountId": "111111111111",
                "ConfigRuleName": "OrgConfigRule-s3-bucket-level-public-access-prohibited-a",
                "Compliance": {"ComplianceType": "COMPLIANT"},
            },
            {
                "AccountId": "111111111111",
                "ConfigRuleName": "OrgConfigRule-restricted-ssh-b",
                "Compliance": {"ComplianceType": "NON_COMPLIANT"},
            },
            {
                "AccountId": "222222222222",
                "ConfigRuleName": "OrgConfigRule-s3-bucket-level-public-access-prohibited-c",
                "Compliance": {"ComplianceType": "COMPLIANT"},
            },
            {
                "AccountId": "222222222222",
                "ConfigRuleName": "OrgConfigRule-restricted-ssh-d",
                "Compliance": {"ComplianceType": "COMPLIANT"},
            },
            {
                "AccountId": "333333333333",
                "ConfigRuleName": "OrgConfigRule-s3-bucket-level-public-access-prohibited-e",
                "Compliance": {"ComplianceType": "INSUFFICIENT_DATA"},
            },
            {
                "AccountId": "333333333333",
                "ConfigRuleName": "OrgConfigRule-restricted-ssh-f",
                "Compliance": {"ComplianceType": "COMPLIANT"},
            },
            {
                "AccountId": "444444444444",
                "ConfigRuleName": "OrgConfigRule-s3-bucket-level-public-access-prohibited-g",
                "Compliance": {"ComplianceType": "COMPLIANT"},
            },
            {
                "AccountId": "444444444444",
                "ConfigRuleName": "OrgConfigRule-restricted-ssh-h",
                "Compliance": {"ComplianceType": "COMPLIANT"},
            },
        ]
    }


class OrgConfigOverviewTests(unittest.TestCase):
    def test_fixed_four_alias_mapping(self):
        targets = parse_targets(RAW)
        self.assertEqual(tuple(targets), ALIASES)
        with self.assertRaises(ValueError):
            parse_targets(json.dumps([{"alias": "lab-dev", "account_id": "111111111111"}]))

    def test_status_is_alias_only_and_live(self):
        result = read_status(RAW, aggregate)
        self.assertEqual(result["scope"], "four-account-live-config")
        self.assertFalse(result["mutation"])
        self.assertEqual([row["alias"] for row in result["accounts"]], list(ALIASES))
        by_alias = {row["alias"]: row["controls"] for row in result["accounts"]}
        self.assertEqual(by_alias["lab-dev"][S3_CONTROL], "COMPLIANT")
        self.assertEqual(by_alias["lab-dev"][SG_CONTROL], "NON_COMPLIANT")
        public = json.dumps(result)
        for account_id in ("111111111111", "222222222222", "333333333333", "444444444444"):
            self.assertNotIn(account_id, public)

    def test_plan_uses_four_accounts_not_legacy_resource_totals(self):
        result = remediation_plan("all", RAW, aggregate)
        self.assertEqual(result["scope"], "four-account-live-config")
        self.assertFalse(result["mutation"])
        self.assertEqual(len(result["plans"]), 2)
        sg = next(x for x in result["plans"] if x["control"] == SG_CONTROL)
        self.assertEqual(sg["noncompliant_aliases"], ["lab-dev"])
        self.assertFalse(sg["chat_execution_available"])
        self.assertNotIn("100", json.dumps(result))
        self.assertNotIn("10 security", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
