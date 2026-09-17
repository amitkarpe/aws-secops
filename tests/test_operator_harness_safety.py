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
        for tool in (
            "@secops_reads/SecOpsRead___get_config_summary",
            "@secops_reads/SecOpsRead___list_config_findings",
            "@secops_reads/SecOpsRead___investigate_s3_context",
            "@secops_reads/SecOpsRead___get_s3_decision_timeline",
            "@secops_reads/SecOpsRead___get_multi_account_security_overview",
            "@secops_reads/SecOpsRead___get_multi_account_control_drill_down",
        ):
            self.assertIn(tool, self.text)
        allowed = self.text.split("AllowedTools:", 1)[1].split("Tools:", 1)[0]
        self.assertNotIn("request_approval", allowed)
        self.assertNotIn("apply_", allowed)
        self.assertNotIn("execute", allowed.lower())
        self.assertNotIn("shell", allowed.lower())

    def test_gateway_policy_is_enforced(self):
        self.assertIn("Mode: ENFORCE", self.text)
        self.assertIn("EnforcementMode: ACTIVE", self.text)
        self.assertIn("FAIL_ON_ANY_FINDINGS", self.text)
        for action in (
            'AgentCore::Action::"SecOpsRead___get_config_summary"',
            'AgentCore::Action::"SecOpsRead___list_config_findings"',
            'AgentCore::Action::"SecOpsRead___investigate_s3_context"',
            'AgentCore::Action::"SecOpsRead___get_s3_decision_timeline"',
            'AgentCore::Action::"SecOpsRead___get_multi_account_security_overview"',
            'AgentCore::Action::"SecOpsRead___get_multi_account_control_drill_down"',
        ):
            self.assertIn(action, self.text)

    def test_config_scope_is_fixed_to_existing_controls(self):
        self.assertIn("s3-bucket-level-public-access-prohibited", self.text)
        self.assertIn("restricted-ssh", self.text)
        self.assertIn("MAX_RESULTS = 250", self.text)
        self.assertIn("MAX_PAGES = 10", self.text)
        self.assertIn("selected[:20]", self.text)
        self.assertIn("if set(event) != {'control'} or event['control'] not in RULES:", self.text)
        self.assertIn("only one exact supported control is accepted", self.text)
        self.assertNotIn("AdditionalProperties:", self.text)
        self.assertNotIn("Enum:", self.text)

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
        read_role = self.text.split("PolicyName: ExactConfigAndDemoS3Reads", 1)[1].split("OperatorReadFunction:", 1)[0]
        self.assertIn("config:GetComplianceDetailsByConfigRule", read_role)
        for required in (
            "s3:GetBucketLocation",
            "s3:GetBucketTagging",
            "s3:GetBucketPublicAccessBlock",
            "s3:GetBucketPolicyStatus",
        ):
            self.assertIn(required, read_role)
        self.assertIn("arn:${AWS::Partition}:s3:::aws-secops-bpa-*", read_role)
        self.assertIn("Sid: ExactMultiAccountReadRoleAssumption", read_role)
        self.assertIn("Action: sts:AssumeRole", read_role)
        self.assertIn("Resource: !Split ['|', !Ref MultiAccountReadRoleArns]", read_role)
        for forbidden in (
            "config:Put",
            "config:Delete",
            "s3:Put",
            "s3:Delete",
            "s3:GetObject",
            "s3:ListAllMyBuckets",
            "ec2:Revoke",
            "ec2:Authorize",
            "ssm:Put",
            "sts:TagSession",
            "sts:SetSourceIdentity",
        ):
            self.assertNotIn(forbidden, read_role)

    def test_multi_account_scope_is_exact_and_identifier_safe(self):
        self.assertIn("MultiAccountReadRoleArns:", self.text)
        self.assertIn("NoEcho: true", self.text)
        self.assertIn(
            r"ChatGPTCrossAccountReadRole(\|arn:aws[a-zA-Z-]*:iam::[0-9]{12}:role/ChatGPTCrossAccountReadRole){3}$'",
            self.text,
        )
        self.assertIn("OVERVIEW_ALIASES = ('lab-dev', 'lab-poc', 'lab-qa', 'lab-sec')", self.text)
        self.assertIn("def multi_account_security_overview(event):", self.text)
        self.assertIn("def multi_account_control_drill_down(event):", self.text)
        self.assertIn("'account_ids': 'hidden-by-default'", self.text)
        self.assertIn("'resource_identifiers': 'not-collected'", self.text)
        self.assertIn("'mutation': False", self.text)
        self.assertIn("'CONFIG_UNAVAILABLE'", self.text)
        self.assertNotIn("sts:TagSession", self.text)

    def test_unhealthy_config_fails_closed_with_structured_output(self):
        self.assertIn("CONFIG_UNAVAILABLE = 'AWS Config recorder is not active and successful'", self.text)
        self.assertIn("x.get('lastStatus') == 'SUCCESS'", self.text)
        self.assertIn("raise RuntimeError(CONFIG_UNAVAILABLE)", self.text)
        self.assertIn("def unavailable_result(tool):", self.text)
        self.assertIn("'status': 'UNVERIFIED'", self.text)
        self.assertIn("'partial': True", self.text)
        self.assertIn("stage('Finding', 'UNVERIFIED'", self.text)
        self.assertIn("stage('Investigation', 'BLOCKED'", self.text)
        self.assertIn("if str(exc) != CONFIG_UNAVAILABLE:", self.text)
        self.assertIn("raise\n                  result = unavailable_result(tool)", self.text)

    def test_write_requests_are_explicitly_refused_by_contract(self):
        self.assertIn("existing governed human-approval path", self.text)
        self.assertIn("do not claim or attempt a change", self.text)
        self.assertIn("If live evidence is unavailable, partial or outside the retained scope, say UNVERIFIED or BLOCKED", self.text)

    def test_operator_summary_contract_is_concise_and_identifier_safe(self):
        self.assertIn("lead with the result", self.text)
        self.assertIn("Prefer one small Markdown table", self.text)
        self.assertIn("✅ compliant/pass", self.text)
        self.assertIn("⚠️ attention/partial", self.text)
        self.assertIn("❌ non-compliant/fail", self.text)
        self.assertIn("ℹ️ informational", self.text)
        self.assertIn("Hide resource IDs, bucket names, ARNs, account IDs and internal identifiers by default", self.text)
        self.assertIn("only when the operator explicitly asks", self.text)
        self.assertIn("no current non-compliant findings were returned by AWS Config", self.text)


if __name__ == "__main__":
    unittest.main()
