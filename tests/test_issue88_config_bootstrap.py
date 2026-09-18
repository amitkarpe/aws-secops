import unittest
from pathlib import Path


class Issue88ConfigBootstrapTests(unittest.TestCase):
    def text(self) -> str:
        path = Path(__file__).resolve().parents[1] / "scripts" / "issue88_config_bootstrap.py"
        value = path.read_text(encoding="utf-8")
        compile(value, str(path), "exec")
        return value

    def test_bootstrap_is_exact_and_public_safe(self):
        text = self.text()
        for token in (
            'TARGETS_ENV = "SECOPS_ISSUE82_TARGETS_JSON"',
            'AccessMode,Value=oidc-lab-admin',
            'AWS::S3::Bucket',
            'AWS::EC2::SecurityGroup',
            'S3_BUCKET_LEVEL_PUBLIC_ACCESS_PROHIBITED',
            'INCOMING_SSH_DISABLED',
            'config-multiaccountsetup.amazonaws.com',
            'AWSConfigRoleForOrganizations',
            'put-configuration-aggregator',
            'put-organization-config-rule',
            '"resource_identifiers": "hidden-by-default"',
            '"account_ids": "hidden-by-default"',
            '"config_remediation": False',
            '"scp_change": False',
        ):
            self.assertIn(token, text)

    def test_org_rule_exclusions_keep_management_account_in_scope(self):
        text = self.text()
        self.assertIn("account_id != management_account and account_id not in target_ids", text)

    def test_bootstrap_does_not_add_auto_remediation_or_scp_mutation(self):
        text = self.text()
        for token in (
            "put-remediation-configuration",
            "put-organization-conformance-pack",
            "attach-policy",
            "create-policy",
            "delete-configuration-recorder",
            "delete-delivery-channel",
            "stop-configuration-recorder",
        ):
            self.assertNotIn(token, text)

    def test_central_delivery_bucket_is_private(self):
        text = self.text()
        for token in (
            '"BlockPublicAcls": True',
            '"IgnorePublicAcls": True',
            '"BlockPublicPolicy": True',
            '"RestrictPublicBuckets": True',
            '"Principal": {"Service": "config.amazonaws.com"}',
            '"aws:SourceOrgID"',
            '"s3:x-amz-acl": "bucket-owner-full-control"',
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
