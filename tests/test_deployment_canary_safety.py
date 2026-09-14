from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ROLE_TEMPLATE = ROOT / "infra" / "github-oidc" / "deploy-canary-role.yml"
CANARY_TEMPLATE = ROOT / "infra" / "deployment-canary" / "template.yml"
WORKFLOW = ROOT / ".github" / "workflows" / "aws-deploy-canary.yml"


class DeploymentCanarySafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.role_template = ROLE_TEMPLATE.read_text(encoding="utf-8")
        cls.canary_template = CANARY_TEMPLATE.read_text(encoding="utf-8")
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_oidc_trust_is_exact_repo_main_only(self):
        expected = "repo:amitkarpe@1894622/aws-secops@1362357126:ref:refs/heads/main"
        self.assertIn(f"Default: {expected}", self.role_template)
        self.assertIn(f"- {expected}", self.role_template)
        self.assertIn("token.actions.githubusercontent.com:aud: sts.amazonaws.com", self.role_template)
        self.assertNotIn("repo:amitkarpe/aws-secops:*", self.role_template)

    def test_deploy_role_is_bounded_to_canary(self):
        self.assertIn("stack/aws-secops-deployment-canary/*", self.role_template)
        self.assertIn("parameter/amitkarpe/aws-secops/deployment-canary", self.role_template)
        policy_section = self.role_template.split("PolicyName: aws-secops-deployment-canary", 1)[1]
        self.assertNotIn("cloudformation:DeleteStack", policy_section)
        self.assertNotIn("- iam:", policy_section.lower())
        self.assertNotIn("- lambda:", policy_section.lower())
        self.assertNotIn("- bedrock-agentcore:", policy_section.lower())

    def test_canary_stack_only_manages_one_ssm_parameter(self):
        self.assertEqual(self.canary_template.count("Type: AWS::SSM::Parameter"), 1)
        self.assertNotIn("AWS::IAM::", self.canary_template)
        self.assertNotIn("AWS::Lambda::", self.canary_template)
        self.assertNotIn("AWS::EC2::", self.canary_template)
        self.assertNotIn("AWS::S3::", self.canary_template)
        self.assertIn("Name: /amitkarpe/aws-secops/deployment-canary", self.canary_template)
        self.assertNotIn("Name: /aws-secops/", self.canary_template)

    def test_workflow_is_manual_main_repo_and_enabled_only(self):
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertNotIn("pull_request:", self.workflow)
        self.assertNotIn("push:", self.workflow)
        self.assertIn("github.ref == 'refs/heads/main'", self.workflow)
        self.assertIn("github.repository == 'amitkarpe/aws-secops'", self.workflow)
        self.assertIn("vars.AWS_DEPLOY_CANARY_ENABLED == 'true'", self.workflow)

    def test_oidc_permission_is_job_scoped_and_actions_are_pinned(self):
        top_level_permissions, jobs = self.workflow.split("jobs:", 1)
        self.assertNotIn("id-token: write", top_level_permissions)
        self.assertIn("id-token: write", jobs)
        self.assertIn("persist-credentials: false", self.workflow)
        self.assertIn("actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803", self.workflow)
        self.assertIn("aws-actions/configure-aws-credentials@61815dcd50bd041e203e49132bacad1fd04d2708", self.workflow)

    def test_workflow_mutation_is_only_canary_stack(self):
        self.assertIn("STACK_NAME: aws-secops-deployment-canary", self.workflow)
        self.assertIn("PARAMETER_NAME: /amitkarpe/aws-secops/deployment-canary", self.workflow)
        forbidden = (
            "aws lambda update-",
            "aws lambda create-",
            "aws ec2 ",
            "aws s3api put-",
            "aws ssm send-command",
            "aws bedrock-agentcore-control create-",
            "aws bedrock-agentcore-control update-",
        )
        for fragment in forbidden:
            self.assertNotIn(fragment, self.workflow)


if __name__ == "__main__":
    unittest.main()
