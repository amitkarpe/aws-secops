import base64
import json
import unittest
from unittest.mock import patch

from pilot_v1 import codebuild_execution
from pilot_v1.multi_account_campaign import S3_CONTROL, SG_CONTROL


class CodeBuildExecutionTests(unittest.TestCase):
    def test_validation_is_exact(self):
        codebuild_execution._validate("plan", S3_CONTROL, None)
        codebuild_execution._validate("execute", SG_CONTROL, "a" * 20)
        with self.assertRaises(ValueError):
            codebuild_execution._validate("execute", SG_CONTROL, "bad")
        with self.assertRaises(ValueError):
            codebuild_execution._validate("plan", S3_CONTROL, "a" * 20)
        with self.assertRaises(ValueError):
            codebuild_execution._validate("execute", "waf", "a" * 20)

    def test_run_uses_fixed_project_and_returns_public_safe_result(self):
        result = {
            "control": S3_CONTROL,
            "batch_id": "a" * 20,
            "decision": "PLAN",
            "mutation_count": 0,
            "provider_verified": False,
            "pending_aliases": ["lab-dev", "lab-poc", "lab-qa", "lab-sec"],
            "account_ids": "hidden-by-default",
            "resource_identifiers": "hidden-by-default",
        }
        encoded = base64.b64encode(json.dumps(result).encode()).decode()

        calls = []
        def fake_json(args):
            calls.append(args)
            if "start-build" in args:
                return {"build": {"id": codebuild_execution.PROJECT + ":1234"}}
            return {
                "builds": [{
                    "buildStatus": "SUCCEEDED",
                    "exportedEnvironmentVariables": [
                        {"name": "SECOPS_RESULT_B64", "value": encoded},
                    ],
                }]
            }

        with patch.object(codebuild_execution, "_json", side_effect=fake_json):
            value = codebuild_execution.run("plan", S3_CONTROL, timeout=1)

        self.assertEqual(value["control"], S3_CONTROL)
        self.assertEqual(value["build_id"], "hidden-by-default")
        start = calls[0]
        self.assertIn(codebuild_execution.PROJECT, start)
        self.assertNotIn("buildspecOverride", json.dumps(start))
        self.assertNotIn("sourceVersionOverride", json.dumps(start))

    def test_source_contains_no_generic_model_selected_overrides(self):
        import pathlib
        root = pathlib.Path(__file__).resolve().parents[1]
        bridge = (root / "pilot_v1" / "codebuild_execution.py").read_text()
        entry = (root / "scripts" / "codebuild_issue82_executor.py").read_text()
        buildspec = (root / "buildspecs" / "secops-four-account-executor.yml").read_text()
        self.assertIn('PROJECT = "aws-secops-four-account-executor"', bridge)
        self.assertNotIn("buildspec-override", bridge)
        self.assertNotIn("source-version-override", bridge)
        self.assertIn("github-actions-aws-platform-lab-read-controller", entry)
        self.assertIn('["--decision", "approve"', entry)
        self.assertIn("SECOPS_RESULT_B64", buildspec)
        self.assertIn('export PYTHONPATH="$CODEBUILD_SRC_DIR"', buildspec)
        self.assertIn('SECOPS_RESULT_B64="$(python3 scripts/codebuild_issue82_executor.py)"', buildspec)
        self.assertNotIn('export SECOPS_RESULT_B64="$(python3', buildspec)
        packager = (root / "scripts" / "prepare-inline-bulk.py").read_text()
        self.assertIn('"pilot_v1/codebuild_execution.py"', packager)
        self.assertIn('"pilot_v1/multi_account_campaign.py"', packager)


if __name__ == "__main__":
    unittest.main()
