from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "infra" / "github-oidc" / "template.yml"
WORKFLOW = ROOT / ".github" / "workflows" / "aws-oidc-preflight.yml"


class OidcPreflightSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = TEMPLATE.read_text(encoding="utf-8")
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_trust_is_exact_repo_main_only(self):
        expected = "repo:amitkarpe/aws-secops:ref:refs/heads/main"
        self.assertIn(f"Default: {expected}", self.template)
        self.assertIn(f"- {expected}", self.template)
        self.assertIn("token.actions.githubusercontent.com:aud: sts.amazonaws.com", self.template)
        self.assertNotIn("repo:amitkarpe/aws-secops:*", self.template)

    def test_preflight_policy_is_read_only(self):
        expected_actions = {
            "config:DescribeConfigurationRecorders",
            "lambda:ListFunctions",
            "bedrock-agentcore:ListGateways",
        }
        for action in expected_actions:
            self.assertIn(f"- {action}", self.template)

        forbidden_verbs = (
            "Create",
            "Delete",
            "Put",
            "Update",
            "Start",
            "Stop",
            "Invoke",
            "Send",
            "Execute",
            "Apply",
        )
        policy_section = self.template.split("PolicyName: aws-secops-readonly-preflight", 1)[1]
        for verb in forbidden_verbs:
            self.assertNotIn(f":{verb}", policy_section)

    def test_workflow_is_manual_exact_repo_and_main_only(self):
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertNotIn("pull_request:", self.workflow)
        self.assertNotIn("push:", self.workflow)
        self.assertIn("github.ref == 'refs/heads/main'", self.workflow)
        self.assertIn("github.repository == 'amitkarpe/aws-secops'", self.workflow)

    def test_oidc_permission_is_job_scoped(self):
        top_level_permissions, jobs = self.workflow.split("jobs:", 1)
        self.assertNotIn("id-token: write", top_level_permissions)
        self.assertIn("id-token: write", jobs)
        self.assertIn("contents: read", top_level_permissions)
        self.assertIn("persist-credentials: false", self.workflow)

    def test_workflow_aws_commands_are_read_only(self):
        expected_commands = (
            "aws sts get-caller-identity",
            "aws configservice describe-configuration-recorders",
            "aws lambda list-functions",
            "aws bedrock-agentcore-control list-gateways",
        )
        for command in expected_commands:
            self.assertIn(command, self.workflow)

        forbidden_fragments = (
            "aws cloudformation deploy",
            "aws cloudformation create-",
            "aws lambda update-",
            "aws lambda create-",
            "aws configservice put-",
            "aws bedrock-agentcore-control create-",
            "aws bedrock-agentcore-control update-",
            "aws ssm send-command",
            "terraform apply",
        )
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, self.workflow)


if __name__ == "__main__":
    unittest.main()
