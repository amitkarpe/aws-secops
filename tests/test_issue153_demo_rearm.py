from __future__ import annotations

import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from pilot_v1.multi_account_campaign import ALIASES, CampaignTarget, S3_CONTROL


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "issue82_campaign_runtime",
    ROOT / "scripts" / "issue82_campaign.py",
)
campaign = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(campaign)


class Issue153DemoRearmRegressionTests(unittest.TestCase):
    def sessions(self):
        rows = []
        for index, alias in enumerate(ALIASES, start=1):
            account_id = f"{index:012d}"
            target = CampaignTarget(
                alias=alias,
                account_id=account_id,
                role_arn=f"arn:aws:iam::{account_id}:role/ChatGPTCrossAccountReadRole",
            )
            rows.append(campaign.TargetSession(target=target, env={}))
        return rows

    @staticmethod
    def bpa(compliant: bool):
        value = compliant
        return {
            "BlockPublicAcls": value,
            "IgnorePublicAcls": value,
            "BlockPublicPolicy": value,
            "RestrictPublicBuckets": value,
        }

    def run_prepare(self, initial):
        sessions = self.sessions()
        state = dict(initial)

        def ensure_bucket(session):
            session.bucket = f"bucket-{session.target.alias}"
            return session.bucket

        def get_bpa(session, _bucket):
            return self.bpa(state[session.target.alias])

        def run(args, **_kwargs):
            if args[:2] == ["s3api", "put-public-access-block"]:
                bucket = args[args.index("--bucket") + 1]
                alias = bucket.removeprefix("bucket-")
                state[alias] = False
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        def frozen_plan(current_sessions, _control, _exclude_resources=None):
            return (
                "a" * 20,
                list(current_sessions),
                {session.target.alias: "NON_COMPLIANT" for session in current_sessions},
                [],
                [],
            )

        with (
            patch.object(campaign, "_ensure_bucket", side_effect=ensure_bucket),
            patch.object(campaign, "_assert_bucket_safe_for_rearm", return_value=None),
            patch.object(campaign, "_get_bpa", side_effect=get_bpa),
            patch.object(campaign, "_run", side_effect=run),
            patch.object(campaign, "_plan_for_control", side_effect=frozen_plan),
        ):
            result = campaign.prepare(sessions, S3_CONTROL)

        return result, state

    def test_mixed_two_compliant_two_noncompliant_rearms_only_two(self):
        result, state = self.run_prepare({
            "lab-dev": True,
            "lab-poc": True,
            "lab-qa": False,
            "lab-sec": False,
        })
        self.assertEqual(result["decision"], "PREPARE")
        self.assertEqual(result["mutation_count"], 2)
        self.assertTrue(result["provider_verified"])
        self.assertEqual(result["aliases"], list(ALIASES))
        self.assertEqual(result["changed_aliases"], ["lab-dev", "lab-poc"])
        self.assertEqual(state, {alias: False for alias in ALIASES})

    def test_already_rearmed_all_four_is_idempotent(self):
        result, state = self.run_prepare({alias: False for alias in ALIASES})
        self.assertEqual(result["mutation_count"], 0)
        self.assertEqual(result["changed_aliases"], [])
        self.assertTrue(result["provider_verified"])
        self.assertEqual(state, {alias: False for alias in ALIASES})

    def test_codebuild_prepare_does_not_pass_selective_account_args(self):
        text = (ROOT / "scripts" / "codebuild_issue82_executor.py").read_text()
        self.assertIn('if mode != "prepare":', text)
        self.assertIn('command += ["--include-account", alias]', text)
        self.assertIn('prepare demo reset remains all-four only', text)


if __name__ == "__main__":
    unittest.main()
