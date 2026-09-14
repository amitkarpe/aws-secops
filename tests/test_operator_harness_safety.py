from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "infra" / "operator-harness" / "template.yml"


class OperatorHarnessSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = TEMPLATE.read_text(encoding="utf-8")

    def test_one_real_operator_harness(self):
        self.assertEqual(self.text.count("Type: AWS::BedrockAgentCore::Harness"), 1)
        self.assertIn("HarnessName: aws_secops_operator", self.text)
        self.assertIn("global.amazon.nova-2-lite-v1:0", self.text)
        self.assertIn("Memory:\n        Disabled: {}", self.text)

    def test_only_exact_read_tools_are_allowed(self):
        self.assertIn("@secops_reads/SecOpsRead___get_config_summary", self.text)
        self.assertIn("@secops_reads/SecOpsRead___list_config_findings", self.text)
        allowed = self.text.split("AllowedTools:", 1)[1].split("Tools:", 1)[0]
        self.assertNotIn("request_approval", allowed)
        self.assertNotIn("apply_", allowed)
        self.assertNotIn("execute", allowed.lower())
        self.assertNotIn("shell", allowed.lower())

    def test_gateway_policy_is_enforced(self):
        self.assertIn("Mode: ENFORCE", self.text)
        self.assertIn("EnforcementMode: ACTIVE", self.text)
        self.assertIn("FAIL_ON_ANY_FINDINGS", self.text)
        self.assertIn('AgentCore::Action::"SecOpsRead___get_config_summary"', self.text)
        self.assertIn('AgentCore::Action::"SecOpsRead___list_config_findings"', self.text)

    def test_config_scope_is_fixed_to_existing_controls(self):
        self.assertIn("s3-bucket-level-public-access-prohibited", self.text)
        self.assertIn("restricted-ssh", self.text)
        self.assertIn("MAX_RESULTS = 250", self.text)
        self.assertIn("MAX_PAGES = 10", self.text)
        self.assertIn("selected[:20]", self.text)
        self.assertIn("AdditionalProperties: false", self.text)

    def test_no_model_accessible_mutation_permissions(self):
        harness_policy = self.text.split("PolicyName: NovaAndExactReadGateway", 1)[1].split("OperatorReadPolicy:", 1)[0]
        for forbidden in (
            "s3:Put",
            "ec2:Revoke",
            "ec2:Authorize",
            "ssm:Put",
            "lambda:InvokeFunction",
            "iam:PassRole",
        ):
            self.assertNotIn(forbidden, harness_policy)
        self.assertIn("bedrock-agentcore:InvokeGateway", harness_policy)
        self.assertIn("bedrock-agentcore:InvokeAgentRuntimeCommandShell", harness_policy)
        self.assertIn("Effect: Deny", harness_policy)

    def test_read_lambda_has_no_aws_write_actions(self):
        read_role = self.text.split("PolicyName: ExactConfigReads", 1)[1].split("OperatorReadFunction:", 1)[0]
        self.assertIn("config:GetComplianceDetailsByConfigRule", read_role)
        for forbidden in (
            "config:Put",
            "config:Delete",
            "s3:Put",
            "ec2:Revoke",
            "ec2:Authorize",
            "ssm:Put",
        ):
            self.assertNotIn(forbidden, read_role)

    def test_write_requests_are_explicitly_refused_by_contract(self):
        self.assertIn("existing governed human-approval path", self.text)
        self.assertIn("do not claim or attempt a change", self.text)
        self.assertIn("If live evidence is unavailable, say UNVERIFIED", self.text)


if __name__ == "__main__":
    unittest.main()
