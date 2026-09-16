from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "infra" / "operator-harness" / "template.yml").read_text(encoding="utf-8")


class OperatorHarnessRecentChangeTests(unittest.TestCase):
    def test_cloudtrail_access_is_read_only_and_region_bounded(self):
        read_role = TEMPLATE.split("PolicyName: ExactConfigAndDemoS3Reads", 1)[1].split("OperatorReadFunction:", 1)[0]
        self.assertIn("Action: cloudtrail:LookupEvents", read_role)
        self.assertIn("aws:RequestedRegion: ap-southeast-1", read_role)
        for forbidden in (
            "cloudtrail:CreateTrail",
            "cloudtrail:UpdateTrail",
            "cloudtrail:DeleteTrail",
            "cloudtrail:StartLogging",
            "cloudtrail:StopLogging",
            "cloudtrail:PutEventSelectors",
            "cloudtrail:PutInsightSelectors",
        ):
            self.assertNotIn(forbidden, read_role)

    def test_recent_change_lookup_is_allowlisted_and_bounded(self):
        for event_name in (
            "PutBucketPublicAccessBlock",
            "DeletePublicAccessBlock",
            "PutBucketPolicy",
            "DeleteBucketPolicy",
            "PutBucketAcl",
        ):
            self.assertIn(repr(event_name), TEMPLATE)
        self.assertIn("MAX_CHANGE_LOOKUP = 50", TEMPLATE)
        self.assertIn("MAX_CHANGE_EVENTS = 5", TEMPLATE)
        self.assertIn("LookupAttributes=[{'AttributeKey': 'ResourceName', 'AttributeValue': bucket}]", TEMPLATE)
        self.assertIn("filtered[:MAX_CHANGE_EVENTS]", TEMPLATE)
        self.assertIn("item.get('EventSource') == 's3.amazonaws.com'", TEMPLATE)

    def test_recent_change_output_suppresses_identity_and_raw_event(self):
        helper = TEMPLATE.split("def recent_s3_changes(bucket):", 1)[1].split("def s3_investigation():", 1)[0]
        self.assertIn("'identity': 'suppressed-by-default'", helper)
        self.assertIn("{'action': name, 'observed_at': iso(when)}", helper)
        for forbidden in (
            "Username",
            "CloudTrailEvent",
            "AccessKeyId",
            "PrincipalId",
            "SessionContext",
        ):
            self.assertNotIn(forbidden, helper)

    def test_change_lookup_only_runs_after_deterministic_owned_selection(self):
        investigation = TEMPLATE.split("def s3_investigation():", 1)[1].split("def stage(name, status, summary, source):", 1)[0]
        owned_guard = investigation.index("if owned_demo_bucket(item['resource_id']):")
        selected_bucket = investigation.index("bucket = selected['resource_id']")
        lookup = investigation.index("changes = recent_s3_changes(bucket)")
        self.assertLess(owned_guard, selected_bucket)
        self.assertLess(selected_bucket, lookup)
        self.assertNotIn("recent_s3_changes(event", investigation)

    def test_non_candidate_paths_are_explicitly_not_evaluated(self):
        self.assertIn("'status': 'NOT_EVALUATED'", TEMPLATE)
        self.assertIn("No current retained-demo finding requires change lookup.", TEMPLATE)
        self.assertIn("Config evidence is partial.", TEMPLATE)
        self.assertIn("No retained-owned candidate passed the ownership guard.", TEMPLATE)

    def test_prompt_forbids_root_cause_or_actor_inference(self):
        self.assertIn("never as proof of actor identity, intent, root cause or business impact", TEMPLATE)
        self.assertIn("direct S3 provider state and change history were not read", TEMPLATE)


if __name__ == "__main__":
    unittest.main()
