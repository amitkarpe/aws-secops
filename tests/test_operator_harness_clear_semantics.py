from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "infra" / "operator-harness" / "template.yml").read_text(encoding="utf-8")


class OperatorHarnessClearSemanticsTests(unittest.TestCase):
    def test_zero_finding_clear_is_explicitly_config_only(self):
        self.assertIn("'provider_state': 'NOT_READ'", TEMPLATE)
        self.assertIn("'risk_context': 'NOT_ASSESSED'", TEMPLATE)
        self.assertIn("Direct S3 provider state was not read", TEMPLATE)
        self.assertIn("provider_evidence': None", TEMPLATE)
        self.assertIn("'recent_changes': recent_changes_not_evaluated", TEMPLATE)

    def test_timeline_does_not_turn_clear_into_provider_or_history_verification(self):
        self.assertIn("stage('Provider Readback', 'NOT_READ'", TEMPLATE)
        self.assertIn("no provider-level or change-history risk conclusion is made", TEMPLATE)
        self.assertIn("provider or CloudTrail investigation; neither was evaluated", TEMPLATE)

    def test_prompt_forbids_zero_finding_provider_overclaim(self):
        self.assertIn("Never say or imply that the bucket is not public, protected, safe, secure, provider-verified or free from exposure", TEMPLATE)
        self.assertIn("direct S3 provider state and change history were not read", TEMPLATE)
        self.assertNotIn("The S3 bucket configuration does not expose public access", TEMPLATE)


if __name__ == "__main__":
    unittest.main()
