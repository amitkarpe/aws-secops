import json
import unittest

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
        with self.assertRaises(ValueError):
            batch_id(S3_CONTROL, list(reversed(refs)))

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
