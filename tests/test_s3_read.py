import json
import unittest

from pilot_v1.s3_lambda import check_s3_allowlist, check_s3_baseline


class MissingConfiguration(Exception):
    def __init__(self, code):
        self.response = {"Error": {"Code": code}}


class FakeS3:
    def get_public_access_block(self, **kwargs):
        return {"PublicAccessBlockConfiguration": {key: True for key in ("BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets")}}

    def get_bucket_encryption(self, **kwargs):
        return {"ServerSideEncryptionConfiguration": {"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}}

    def get_bucket_versioning(self, **kwargs):
        return {"Status": "Enabled"}

    def get_bucket_policy(self, Bucket):
        arn = f"arn:aws:s3:::{Bucket}"
        return {"Policy": json.dumps({"Statement": [{"Effect": "Deny", "Action": "s3:*", "Resource": [arn, f"{arn}/*"], "Condition": {"Bool": {"aws:SecureTransport": "false"}}}]})}

    def get_bucket_ownership_controls(self, **kwargs):
        return {"OwnershipControls": {"Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]}}


class MissingPolicyS3(FakeS3):
    def get_bucket_policy(self, **kwargs):
        raise MissingConfiguration("NoSuchBucketPolicy")


class S3ReadTest(unittest.TestCase):
    def test_five_controls_pass_without_mutation(self):
        result = check_s3_baseline(FakeS3(), "pilot-bucket")
        self.assertEqual(result["status"], "COMPLIANT")
        self.assertEqual(len(result["controls"]), 5)
        self.assertTrue(all(item["status"] == "PASS" for item in result["controls"]))
        self.assertEqual(result["mutation"], "none")

    def test_missing_transport_policy_is_visible_failure(self):
        result = check_s3_baseline(MissingPolicyS3(), "pilot-bucket")
        self.assertEqual(result["status"], "NON_COMPLIANT")
        self.assertEqual(result["controls"][3]["status"], "FAIL")

    def test_allowlist_is_bounded_and_returns_only_exception_detail(self):
        class OneExceptionS3(FakeS3):
            def get_bucket_versioning(self, Bucket):
                return {} if Bucket == "pilot-two" else {"Status": "Enabled"}

        result = check_s3_allowlist(OneExceptionS3(), ["pilot-one", "pilot-two"])
        self.assertEqual(result["buckets_checked"], 2)
        self.assertEqual((result["controls_checked"], result["pass_count"], result["fail_count"]), (10, 9, 1))
        self.assertEqual(result["exceptions"][0]["control"], "Versioning")
        self.assertNotIn("controls", result)
        self.assertEqual(result["mutation"], "none")
        with self.assertRaisesRegex(ValueError, "1 to 5"):
            check_s3_allowlist(FakeS3(), [f"bucket-{index}" for index in range(6)])


if __name__ == "__main__":
    unittest.main()
