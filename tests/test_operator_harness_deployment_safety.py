from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ROLE_TEMPLATE = ROOT / "infra" / "github-oidc" / "operator-harness-deploy-role.yml"
HARNESS_TEMPLATE = ROOT / "infra" / "operator-harness" / "template.yml"
WORKFLOW = ROOT / ".github" / "workflows" / "aws-deploy-operator-harness.yml"


class OperatorHarnessDeploymentSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.role_template = ROLE_TEMPLATE.read_text(encoding="utf-8")
        cls.harness_template = HARNESS_TEMPLATE.read_text(encoding="utf-8")
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_oidc_trust_is_exact_repo_main_only(self):
        expected = "repo:amitkarpe@1894622/aws-secops@1362357126:ref:refs/heads/main"
        self.assertIn(f"Default: {expected}", self.role_template)
        self.assertIn(f"- {expected}", self.role_template)
        self.assertIn("token.actions.githubusercontent.com:aud: sts.amazonaws.com", self.role_template)
        self.assertNotIn("repo:amitkarpe/aws-secops:*", self.role_template)

    def test_github_role_only_manages_exact_stack_and_passes_exact_execution_role(self):
        deploy_policy = self.role_template.split("PolicyName: aws-secops-operator-harness-deploy", 1)[1]
        self.assertIn("stack/aws-secops-operator-harness/*", deploy_policy)
        self.assertIn("iam:PassedToService: cloudformation.amazonaws.com", deploy_policy)
        self.assertNotIn("cloudformation:DeleteStack", deploy_policy)
        for forbidden in ("lambda:", "bedrock-agentcore:", "s3:", "ec2:", "ssm:"):
            self.assertNotIn(forbidden, deploy_policy.lower())

    def test_stack_execution_role_is_bounded_to_operator_resource_families(self):
        stack_policy = self.role_template.split("PolicyName: aws-secops-operator-harness-stack", 1)[1]
        for name in (
            "role/aws-secops-operator-read",
            "role/aws-secops-operator-gateway",
            "role/aws-secops-operator-harness",
            "function:aws-secops-operator-read",
            "log-group:/aws/lambda/aws-secops-operator-read",
        ):
            self.assertIn(name, stack_policy)
        self.assertNotIn("bedrock-agentcore:*", stack_policy)
        self.assertIn("bedrock-agentcore:CreateWorkloadIdentity", stack_policy)
        self.assertIn("bedrock-agentcore:DeleteWorkloadIdentity", stack_policy)
        self.assertIn("bedrock-agentcore:CreateAgentRuntimeEndpoint", stack_policy)
        self.assertIn("bedrock-agentcore:DeleteAgentRuntimeEndpoint", stack_policy)
        for forbidden in ("s3:", "ec2:", "ssm:", "dynamodb:"):
            self.assertNotIn(forbidden, stack_policy.lower())
        self.assertIn("aws:RequestedRegion: ap-southeast-1", stack_policy)

    def test_workflow_is_manual_main_repo_and_explicitly_enabled(self):
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertNotIn("pull_request:", self.workflow)
        self.assertNotIn("push:", self.workflow)
        self.assertIn("github.ref == 'refs/heads/main'", self.workflow)
        self.assertIn("github.repository == 'amitkarpe/aws-secops'", self.workflow)
        self.assertIn("vars.AWS_OPERATOR_HARNESS_DEPLOY_ENABLED == 'true'", self.workflow)
        self.assertIn("AWS_REGION: ${{ vars.AWS_REGION }}", self.workflow)
        for secret in (
            "AWS_ALLOWED_ACCOUNT_ID",
            "AWS_SECOPS_OPERATOR_HARNESS_DEPLOY_ROLE_ARN",
            "AWS_SECOPS_OPERATOR_HARNESS_STACK_EXECUTION_ROLE_ARN",
        ):
            self.assertIn(f"secrets.{secret}", self.workflow)
            self.assertNotIn(f"vars.{secret}", self.workflow)

    def test_oidc_permission_is_job_scoped_and_actions_are_pinned(self):
        top_level_permissions, jobs = self.workflow.split("jobs:", 1)
        self.assertNotIn("id-token: write", top_level_permissions)
        self.assertIn("id-token: write", jobs)
        self.assertIn("persist-credentials: false", self.workflow)
        self.assertIn("actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803", self.workflow)
        self.assertIn("aws-actions/configure-aws-credentials@61815dcd50bd041e203e49132bacad1fd04d2708", self.workflow)

    def test_workflow_mutates_only_operator_harness_cloudformation_stack(self):
        self.assertIn("STACK_NAME: aws-secops-operator-harness", self.workflow)
        self.assertIn("TEMPLATE_PATH: infra/operator-harness/template.yml", self.workflow)
        self.assertIn("--role-arn \"$AWS_STACK_EXECUTION_ROLE_ARN\"", self.workflow)
        self.assertIn("--capabilities CAPABILITY_NAMED_IAM", self.workflow)
        self.assertNotIn("delete-stack", self.workflow)
        forbidden = (
            "aws lambda ",
            "aws iam ",
            "aws ec2 ",
            "aws s3",
            "aws ssm ",
            "aws bedrock-agentcore",
        )
        for fragment in forbidden:
            self.assertNotIn(fragment, self.workflow)

    def test_existing_harness_contract_remains_read_only(self):
        self.assertIn("HarnessName: aws_secops_operator", self.harness_template)
        self.assertIn("Mode: ENFORCE", self.harness_template)
        for tool in (
            "@secops_reads/SecOpsRead___get_config_summary",
            "@secops_reads/SecOpsRead___list_config_findings",
            "@secops_reads/SecOpsRead___investigate_s3_context",
            "@secops_reads/SecOpsRead___get_s3_decision_timeline",
        ):
            self.assertIn(tool, self.harness_template)
        for forbidden in (
            "ssm:SendCommand",
            "ec2:RevokeSecurityGroupIngress",
            "s3:PutBucketPublicAccessBlock",
            "s3:PutBucketPolicy",
            "s3:DeleteBucket",
            "s3:GetObject",
            "s3:ListAllMyBuckets",
        ):
            self.assertNotIn(forbidden, self.harness_template)

    def test_harness_native_s3_investigation_is_exact_read_only_scope(self):
        for action in (
            "s3:GetBucketLocation",
            "s3:GetBucketTagging",
            "s3:GetBucketPublicAccessBlock",
            "s3:GetBucketPolicyStatus",
        ):
            self.assertIn(action, self.harness_template)
        self.assertIn("arn:${AWS::Partition}:s3:::aws-secops-bpa-*", self.harness_template)
        self.assertIn("DEMO_PREFIX = 'aws-secops-bpa-'", self.harness_template)
        for tag in (
            "'owner': 'amit'",
            "'phase': 'bulk-bpa'",
            "'project': 'aws-secops'",
            "'environment': 'dev'",
            "'version': 'r01'",
        ):
            self.assertIn(tag, self.harness_template)
        self.assertIn("No remediation tool is available to this read-only Harness.", self.harness_template)
        self.assertIn("chain_of_thought': 'not-collected-and-not-displayed'", self.harness_template)

    def test_new_harness_tools_take_no_model_selected_resource_input(self):
        investigation = self.harness_template.split("- Name: investigate_s3_context", 1)[1].split("- Name: get_s3_decision_timeline", 1)[0]
        timeline = self.harness_template.split("- Name: get_s3_decision_timeline", 1)[1].split("OperatorHarnessRole:", 1)[0]
        for block in (investigation, timeline):
            self.assertIn("Properties: {}", block)
            self.assertNotIn("bucket:", block.lower())
            self.assertNotIn("resource_id", block.lower())


if __name__ == "__main__":
    unittest.main()
