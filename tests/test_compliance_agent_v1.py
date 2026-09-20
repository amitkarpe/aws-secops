from __future__ import annotations

import asyncio
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "agents" / "compliance-agent-v1" / "src"
sys.path.insert(0, str(SRC))

from compliance_agent_v1 import agent, config_backend, harness_client  # noqa: E402


def snapshot():
    rules = []
    for alias in config_backend.ALIASES:
        for control in config_backend.CONTROLS:
            rules.append({
                "accountAlias": alias,
                "ConfigRuleName": control,
                "status": "NON_COMPLIANT",
                "count": 1,
            })
    return {
        "environment": "ALL", "available": True, "partial": False,
        "availableAccounts": 4, "totalAccounts": 4,
        "fetchedAt": "2026-09-20T05:00:00Z",
        "accounts": [{"alias": x, "available": True} for x in config_backend.ALIASES],
        "rules": rules,
    }


class ConfigBackendTests(unittest.TestCase):
    def test_exact_four_account_matrix(self):
        values = {
            "/api/diagnostics": {"status": "DEGRADED", "components": {"configProvider": {"status": "READY"}}},
            "/api/controls?environment=ALL&refresh=1": snapshot(),
        }
        with patch.object(config_backend, "_get_json", side_effect=lambda _base, path: values[path]):
            value = config_backend.current_evidence()
        self.assertEqual(value["aliases"], list(config_backend.ALIASES))
        self.assertEqual(value["controls"], list(config_backend.CONTROLS))
        self.assertEqual(len(value["checks"]), 8)
        self.assertFalse(value["identifiers_available"])
        self.assertTrue(value["read_only"])

    def test_incomplete_matrix_fails_closed(self):
        bad = snapshot()
        bad["rules"] = bad["rules"][:-1]
        values = {
            "/api/diagnostics": {"components": {"configProvider": {"status": "READY"}}},
            "/api/controls?environment=ALL&refresh=1": bad,
        }
        with patch.object(config_backend, "_get_json", side_effect=lambda _base, path: values[path]):
            with self.assertRaises(config_backend.BackendEvidenceError):
                config_backend.current_evidence()

    def test_loopback_backend_only(self):
        with self.assertRaises(config_backend.BackendEvidenceError):
            config_backend._base("https://example.com")


class HarnessClientTests(unittest.TestCase):
    def test_invoke_harness_text_stream(self):
        class Client:
            def invoke_harness(self, **kwargs):
                self.kwargs = kwargs
                return {"stream": iter([
                    {"contentBlockDelta": {"delta": {"text": "Compliance "}}},
                    {"contentBlockDelta": {"delta": {"text": "Agent v1"}}},
                ])}
        client = Client()
        arn = "arn:aws:bedrock-agentcore:ap-southeast-1:123456789012:harness/compliance_agent_v1-AbC123"
        value = harness_client.invoke("evidence", arn, client=client)
        self.assertEqual(value["answer"], "Compliance Agent v1")
        self.assertEqual(client.kwargs["maxIterations"], 1)

    def test_tool_event_rejected(self):
        class Client:
            def invoke_harness(self, **kwargs):
                return {"stream": iter([{"contentBlockStart": {"start": {"toolUse": {"name": "x"}}}}])}
        arn = "arn:aws:bedrock-agentcore:ap-southeast-1:123456789012:harness/compliance_agent_v1-AbC123"
        with self.assertRaises(harness_client.HarnessError):
            harness_client.invoke("evidence", arn, client=Client())

    def test_invalid_harness_response_is_sanitized(self):
        class Client:
            def invoke_harness(self, **kwargs):
                return "not-an-object"
        arn = "arn:aws:bedrock-agentcore:ap-southeast-1:123456789012:harness/compliance_agent_v1-AbC123"
        with self.assertRaisesRegex(harness_client.HarnessError, "invalid response"):
            harness_client.invoke("evidence", arn, client=Client())

    def test_stream_failure_is_sanitized(self):
        def broken():
            yield {"contentBlockDelta": {"delta": {"text": "partial"}}}
            raise RuntimeError("private provider detail")

        class Client:
            def invoke_harness(self, **kwargs):
                return {"stream": broken()}

        arn = "arn:aws:bedrock-agentcore:ap-southeast-1:123456789012:harness/compliance_agent_v1-AbC123"
        with self.assertRaisesRegex(harness_client.HarnessError, "stream failed") as error:
            harness_client.invoke("evidence", arn, client=Client())
        self.assertNotIn("private provider detail", str(error.exception))


class AgentTests(unittest.TestCase):
    def test_answer_uses_evidence_and_no_mutation(self):
        evidence = {
            "version": 1, "source": "Unified Config backend", "fetched_at": "now",
            "aliases": list(config_backend.ALIASES), "controls": list(config_backend.CONTROLS),
            "checks": [{"account_alias": "lab-dev", "control": config_backend.CONTROLS[0],
                        "status": "NON_COMPLIANT", "affected_resources": 1}],
            "identifiers_available": False, "diagnostics": {"config_provider": "READY"},
            "read_only": True,
        }
        def fake(prompt, arn, region):
            self.assertIn("AUTHORITATIVE_EVIDENCE_JSON", prompt)
            self.assertIn("requires the separate governed approval/execution path", prompt)
            return {"answer": "grounded", "session_id": "x", "events": 1}
        with patch.object(agent, "current_evidence", return_value=evidence):
            value = agent.answer("status", harness_arn="arn:any", harness_call=fake)
        self.assertEqual(value["runtime"], "Amazon Bedrock AgentCore Harness")
        self.assertFalse(value["mutation"])

    def test_invalid_request_fails_before_backend_read(self):
        with patch.object(agent, "current_evidence") as evidence:
            with self.assertRaisesRegex(ValueError, "user request is invalid"):
                agent.answer("   ", harness_arn="arn:any")
        evidence.assert_not_called()


class McpServerRegressionTests(unittest.TestCase):
    def test_mcp_stdio_initializes_with_one_strict_tool(self):
        async def probe():
            env = dict(os.environ)
            env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
            env["AWS_EC2_METADATA_DISABLED"] = "true"
            params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "compliance_agent_v1.mcp_server"],
                env=env,
            )
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    self.assertEqual([tool.name for tool in tools.tools], ["ask_compliance_agent_v1"])

        asyncio.run(probe())

    def test_mcp_argument_model_rejects_unexpected_arguments(self):
        from compliance_agent_v1.mcp_server import mcp

        tools = mcp._tool_manager.list_tools()
        self.assertEqual([tool.name for tool in tools], ["ask_compliance_agent_v1"])
        model = tools[0].fn_metadata.arg_model
        with self.assertRaises(ValidationError):
            model.model_validate({"request": "status", "unexpected": "blocked"})


class RepoIsolationTests(unittest.TestCase):
    def test_v1_integration_is_isolated_from_legacy(self):
        installer = (ROOT / "integration" / "install-compliance-v1.cjs").read_text()
        spec = json.loads((ROOT / "integration" / "compliance-agent-v1.json").read_text())
        combined = installer + json.dumps(spec)
        self.assertNotIn("localhost:4444", combined)
        self.assertNotIn("pilot_v1", combined)
        self.assertIn("compliance_agent_v1", combined)
        self.assertEqual(spec["name"], "Compliance Agent v1")
        self.assertEqual(spec["tools"], ["ask_compliance_agent_v1_mcp_compliance_agent_v1"])

    def test_access_helper_is_bounded_and_idempotent(self):
        helper = (ROOT / "integration" / "ensure-compliance-v1-access.cjs").read_text()
        self.assertIn("AWS Compliance Agent", helper)
        self.assertIn("Compliance Agent v1", helper)
        self.assertIn("target user must already have source-agent access", helper)
        self.assertIn("conflicting target ACL; manual review required", helper)
        self.assertIn("findOne", helper)
        self.assertIn("insertOne", helper)
        self.assertNotIn("deleteOne", helper)
        self.assertNotIn("amitkarpe@", helper)

    def test_harness_is_dedicated_no_tool_runtime(self):
        template = (ROOT / "agents" / "compliance-agent-v1" / "infra" / "template.yml").read_text()
        self.assertIn("HarnessName: compliance_agent_v1", template)
        self.assertIn("AllowedTools: []", template)
        self.assertIn("Tools: []", template)
        self.assertIn("bedrock-agentcore:InvokeGateway", template)
        self.assertIn("Effect: Deny", template)
        self.assertNotIn("4444", template)


if __name__ == "__main__":
    unittest.main()
