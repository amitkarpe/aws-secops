import json
import unittest
from pathlib import Path

from pilot_v1.multi_account_campaign import (
    ALIASES,
    S3_CONTROL,
    SG_CONTROL,
    batch_id,
    has_unrestricted_ssh,
    normalize_config_state,
    parse_targets,
    public_result,
    public_timeline,
    s3_bpa_compliant,
)


class Issue82CampaignContractTests(unittest.TestCase):
    def targets(self):
        rows = []
        for i, alias in enumerate(ALIASES, start=1):
            account = f"{i:012d}"
            rows.append({
                "alias": alias,
                "account_id": account,
                "role_arn": f"arn:aws:iam::{account}:role/ChatGPTCrossAccountReadRole",
            })
        return json.dumps(rows)

    def test_exact_four_aliases_and_roles(self):
        targets = parse_targets(self.targets())
        self.assertEqual(tuple(x.alias for x in targets), ALIASES)
        with self.assertRaises(ValueError):
            parse_targets(json.dumps(json.loads(self.targets())[:3]))

    def test_s3_provider_truth_requires_all_four_bpa_settings(self):
        good = {
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        }
        self.assertTrue(s3_bpa_compliant(good))
        good["RestrictPublicBuckets"] = False
        self.assertFalse(s3_bpa_compliant(good))
        self.assertFalse(s3_bpa_compliant(None))

    def test_sg_provider_truth_is_exact_unrestricted_tcp22(self):
        bad = [{
            "IpProtocol": "tcp",
            "FromPort": 22,
            "ToPort": 22,
            "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
        }]
        self.assertTrue(has_unrestricted_ssh(bad))
        bad[0]["FromPort"] = 443
        bad[0]["ToPort"] = 443
        self.assertFalse(has_unrestricted_ssh(bad))

    def test_config_lag_never_overrides_provider_success(self):
        self.assertEqual(
            normalize_config_state("NON_COMPLIANT", provider_compliant=True),
            "PENDING",
        )
        self.assertEqual(
            normalize_config_state("COMPLIANT", provider_compliant=True),
            "COMPLIANT",
        )
        self.assertEqual(
            normalize_config_state(None, provider_compliant=False),
            "UNAVAILABLE",
        )

    def test_frozen_batch_is_control_specific_and_alias_ordered(self):
        refs = [(alias, f"{i:012x}") for i, alias in enumerate(ALIASES, start=1)]
        s3 = batch_id(S3_CONTROL, refs)
        sg = batch_id(SG_CONTROL, refs)
        self.assertNotEqual(s3, sg)
        self.assertEqual(s3, batch_id(S3_CONTROL, refs))
        excluded = batch_id(S3_CONTROL, refs, ["lab-dev"])
        self.assertNotEqual(s3, excluded)
        self.assertEqual(excluded, batch_id(S3_CONTROL, refs, ["lab-dev"]))
        with self.assertRaises(ValueError):
            batch_id(S3_CONTROL, list(reversed(refs)))
        with self.assertRaises(ValueError):
            batch_id(S3_CONTROL, refs, ["lab-poc", "lab-dev"])
        with self.assertRaises(ValueError):
            batch_id(S3_CONTROL, refs, ["lab-dev", "lab-dev"])

    def test_public_result_hides_identifiers_and_caps_mutations(self):
        states = {alias: "PENDING" for alias in ALIASES}
        result = public_result(
            control=S3_CONTROL,
            batch="a" * 20,
            aliases=ALIASES,
            decision="APPROVE",
            mutation_count=4,
            provider_verified=True,
            config_states=states,
        )
        self.assertEqual(result["account_ids"], "hidden-by-default")
        self.assertEqual(result["resource_identifiers"], "hidden-by-default")
        self.assertFalse(result["harness_mutation"])
        self.assertEqual(result["oidc_session"], "AccessMode=oidc-lab-admin")
        prepared = public_result(
            control=SG_CONTROL,
            batch="b" * 20,
            aliases=ALIASES,
            decision="PREPARE",
            mutation_count=4,
            provider_verified=True,
            config_states=states,
        )
        self.assertEqual(prepared["decision"], "PREPARE")
        with self.assertRaises(ValueError):
            public_result(
                control=S3_CONTROL,
                batch="a" * 20,
                aliases=ALIASES,
                decision="APPROVE",
                mutation_count=5,
                provider_verified=True,
                config_states=states,
            )

    def test_runtime_script_is_syntax_valid_and_keeps_plan_read_only(self):
        path = Path(__file__).resolve().parents[1] / "scripts" / "issue82_campaign.py"
        text = path.read_text(encoding="utf-8")
        compile(text, str(path), "exec")
        plan_section = text.split("def _plan_for_control", 1)[1].split("def plan(", 1)[0]
        self.assertNotIn("_ensure_bucket(", plan_section)
        self.assertNotIn("_ensure_sg(", plan_section)
        self.assertIn("_find_bucket(", plan_section)
        self.assertIn("_find_sg(", plan_section)
        self.assertIn("AccessMode", text)
        self.assertIn("oidc-lab-admin", text)
        self.assertIn("put-public-access-block", text)
        self.assertIn("revoke-security-group-ingress", text)
        self.assertIn("def prepare(sessions: list[TargetSession], control: str)", text)
        self.assertIn("changed_aliases", text)
        self.assertIn("four-account prepare did not leave exactly four non-compliant demo targets", text)
        self.assertIn("--exclude-resource", text)
        self.assertIn("one or more exclusion resources did not resolve exactly", text)
        self.assertIn("excluded resource is not currently non-compliant", text)
        self.assertIn("required for idempotent timeout reconciliation", text)
        self.assertNotIn("exclusions removed every remediation target", text)
        self.assertIn("resource_names = {sg_id, _sg_name(session.target)}", text)
        self.assertIn("batch_id(control, refs, excluded_aliases)", text)
        self.assertIn("SourceIdentifier", text)
        self.assertIn("S3_BUCKET_LEVEL_PUBLIC_ACCESS_PROHIBITED", text)
        self.assertIn("INCOMING_SSH_DISABLED", text)
        self.assertNotIn("put-bucket-policy", text)
        self.assertNotIn("put-object", text)

    def test_decision_timeline_keeps_config_separate(self):
        timeline = public_timeline(
            control=SG_CONTROL,
            config_state="NON_COMPLIANT",
            approved=True,
            provider_verified=True,
            changed=True,
        )
        by_stage = {x["stage"]: x["status"] for x in timeline}
        self.assertEqual(by_stage["Provider Readback"], "VERIFIED")
        self.assertEqual(by_stage["Config Result"], "PENDING")
        self.assertEqual(by_stage["Exact Tool"], "CALLED")


if __name__ == "__main__":
    unittest.main()
