import json
import os
import unittest
from unittest.mock import patch

from pilot_v1.config import DEFAULT_MODEL_ID, DEFAULT_REGION, PilotConfig
from pilot_v1.harness import invoke


class FoundationTest(unittest.TestCase):
    def test_defaults_and_private_values_are_environment_owned(self):
        with patch.dict(os.environ, {}, clear=True):
            config = PilotConfig.from_env()
        self.assertEqual(config.region, DEFAULT_REGION)
        self.assertEqual(config.model_id, DEFAULT_MODEL_ID)
        self.assertEqual(config.harness_arn, "")
        with self.assertRaisesRegex(ValueError, "PILOT_HARNESS_ARN"):
            config.require_harness()

    @patch("pilot_v1.harness.subprocess.run")
    def test_harness_wrapper_returns_text_and_counts_tool_calls(self, run):
        run.return_value.returncode = 0
        run.return_value.stderr = ""
        run.return_value.stdout = "\n".join(
            [
                json.dumps({"start": {"toolUse": {"name": "exact_tool"}}}),
                json.dumps(
                    {
                        "success": True,
                        "response": json.dumps(
                            {"text": "FOUNDATION_OK", "sessionId": "private"}
                        ),
                    }
                ),
            ]
        )
        config = PilotConfig(DEFAULT_REGION, DEFAULT_MODEL_ID, "arn:test", "", "", "", "")
        result = invoke(config, "test", cli="agentcore")
        self.assertEqual(result["response"], "FOUNDATION_OK")
        self.assertEqual(result["tool_calls"], 1)
        command = run.call_args.args[0]
        self.assertIn("--harness-arn", command)
        self.assertNotIn("--tools", command)

    @patch("pilot_v1.harness.subprocess.run")
    def test_harness_wrapper_uses_verbose_text_deltas_when_summary_is_empty(self, run):
        run.return_value.returncode = 0
        run.return_value.stderr = ""
        run.return_value.stdout = "\n".join(
            [
                json.dumps({"delta": {"text": "STATUS: "}}),
                json.dumps({"delta": {"text": "NON_COMPLIANT"}}),
                json.dumps({"success": True, "response": '{"text":""}'}),
            ]
        )
        config = PilotConfig(DEFAULT_REGION, DEFAULT_MODEL_ID, "arn:test", "", "", "", "")
        self.assertEqual(invoke(config, "test")["response"], "STATUS: NON_COMPLIANT")

    @patch("pilot_v1.harness.subprocess.run")
    def test_explanation_restricts_tools_and_rejects_tool_events(self, run):
        run.return_value.returncode = 0
        run.return_value.stdout = json.dumps({"success": True, "response": "Source explanation"})
        config = PilotConfig(DEFAULT_REGION, DEFAULT_MODEL_ID, "arn:test", "", "", "", "")
        result = invoke(config, "evidence", system_prompt="specialist", explanation_only=True)
        self.assertEqual(result["tool_calls"], 0)
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("--allowed-tools") + 1], "__pilot_explanation_no_tools__")
        self.assertEqual(command[command.index("--system-prompt") + 1], "specialist")
        run.return_value.stdout = json.dumps({"start": {"toolUse": {"name": "shell"}}})
        with self.assertRaisesRegex(RuntimeError, "tool call"):
            invoke(config, "evidence", explanation_only=True)


if __name__ == "__main__":
    unittest.main()
