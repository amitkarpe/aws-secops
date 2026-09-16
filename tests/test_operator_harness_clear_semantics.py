from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "infra" / "operator-harness" / "template.yml").read_text(encoding="utf-8")


class OperatorHarnessClearSemanticsTests(unittest.TestCase):
    def test_zero_finding_clear_is_explicitly_config_only(self):
        self.assertIn("'provider_state': 'NOT_READ'", TEMPLATE)
        self.assertIn("'risk_context': 'NOT_ASSESSED'", TEMPLATE)
        self.assertIn("'evidence_boundary': 'Config-only CLEAR does not establish current provider state or absence of exposure/risk.'", TEMPLATE)
        self.assertIn("'confidence_scope': 'HIGH confidence only that AWS Config returned no current retained-demo non-compliant finding; provider state and exposure/risk were not assessed.'", TEMPLATE)
        self.assertIn("Direct S3 provider state and exposure/risk were not assessed", TEMPLATE)
        self.assertIn("provider_evidence': None", TEMPLATE)
        self.assertIn("'recent_changes': recent_changes_not_evaluated", TEMPLATE)

    def test_timeline_does_not_turn_clear_into_provider_or_history_verification(self):
        self.assertIn("stage('Provider Readback', 'NOT_READ'", TEMPLATE)
        self.assertIn("stage('Risk / Context', 'NOT_ASSESSED', inv['evidence_boundary']", TEMPLATE)
        self.assertIn("provider or CloudTrail investigation; neither was evaluated", TEMPLATE)

    def test_prompt_forbids_zero_finding_provider_and_risk_overclaim(self):
        self.assertIn("the CLEAR result is not evidence that exposure or risk is absent", TEMPLATE)
        self.assertIn('Never say or imply \\"no risk\\", \\"low risk\\", \\"no exposure risk is indicated\\"', TEMPLATE)
        self.assertIn('that the buckets \\"appear safe\\"', TEMPLATE)
        self.assertIn('or that they \\"appear compliant\\" beyond the narrow statement', TEMPLATE)
        self.assertIn("Never say or imply that the bucket is not public, protected, safe, secure, provider-verified or free from exposure", TEMPLATE)
        self.assertIn("direct S3 provider state and change history were not read", TEMPLATE)
        self.assertNotIn("The S3 bucket configuration does not expose public access", TEMPLATE)


if __name__ == "__main__":
    unittest.main()
