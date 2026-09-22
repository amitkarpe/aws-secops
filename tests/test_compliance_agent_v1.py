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
        with self.assertRaisesRegex(config_backend.BackendEvidenceError, "port 1111"):
            config_backend._base("http://127.0.0.1:4444")

    def test_empty_resource_ids_are_not_reported_available(self):
        row = {
            "accountId": "",
            "resourceId": "",
            "resourceIds": [],
        }
        self.assertEqual(config_backend._optional_identifiers(row), {})

    def test_nonempty_resource_ids_are_preserved(self):
        self.assertEqual(
            config_backend._optional_identifiers({"resourceIds": ["bucket-a"]}),
            {"resource_ids": ["bucket-a"]},
        )

    def test_resource_ids_are_bounded_and_truthfully_marked(self):
        values = [f"resource-{i}" for i in range(10)]
        result = config_backend._optional_identifiers({
            "accountId": "123456789012",
            "resourceId": "primary-resource",
            "resourceIds": values,
        })
        self.assertEqual(result["account_id"], "123456789012")
        self.assertEqual(result["resource_id"], "primary-resource")
        self.assertEqual(result["resource_ids"], values[:config_backend.MAX_RESOURCE_IDS])
        self.assertTrue(result["resource_ids_truncated"])
        self.assertEqual(result["resource_ids_supplied"], 10)

    def test_ambiguous_identifier_fields_are_omitted(self):
        result = config_backend._optional_identifiers({
            "accountId": "123456789012",
            "AccountId": "999999999999",
            "resourceId": "one",
            "ResourceId": "two",
        })
        self.assertNotIn("account_id", result)
        self.assertNotIn("resource_id", result)

    def test_oversized_backend_response_fails_closed(self):
        class Response:
            status = 200
            headers = {"content-type": "application/json"}
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, _limit):
                return b"x" * (config_backend.MAX_BACKEND_BYTES + 1)

        class Opener:
            def open(self, *_args, **_kwargs):
                return Response()

        with patch.object(config_backend, "build_opener", return_value=Opener()):
            with self.assertRaisesRegex(config_backend.BackendEvidenceError, "too large"):
                config_backend._get_json("http://127.0.0.1:1111", "/api/diagnostics")


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

    def test_tooluse_word_in_normal_text_is_not_a_tool_event(self):
        class Client:
            def invoke_harness(self, **kwargs):
                return {"stream": iter([
                    {"contentBlockDelta": {"delta": {"text": "The word toolUse is ordinary answer text."}}},
                ])}
        arn = "arn:aws:bedrock-agentcore:ap-southeast-1:123456789012:harness/compliance_agent_v1-AbC123"
        value = harness_client.invoke("evidence", arn, client=Client())
        self.assertIn("toolUse", value["answer"])

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
            self.assertIn("governed native approval/execution path", prompt)
            self.assertNotIn("execution is not available in Compliance Agent v1", prompt)
            return {"answer": "grounded", "session_id": "x", "events": 1}
        with patch.object(agent, "current_evidence", return_value=evidence):
            value = agent.answer("status", harness_arn="arn:any", harness_call=fake)
        self.assertEqual(value["runtime"], "Amazon Bedrock AgentCore Harness")
        self.assertEqual(value["evidence"]["check_count"], 1)
        self.assertEqual(len(value["evidence"]["checks"]), 1)
        self.assertFalse(value["mutation"])

    def test_present_answer_normalizes_legacy_read_only_wording(self):
        text = (
            "Compliance Agent v1 cannot execute changes directly. "
            "No execution capability. Compliance Agent v1 can only report status. "
            "Provider-level verification belongs to the provider readback path."
        )
        value = agent._present_answer(text)
        self.assertNotIn("cannot execute changes", value.lower())
        self.assertNotIn("no execution capability", value.lower())
        self.assertNotIn("can only report status", value.lower())
        self.assertNotIn("provider", value.lower())
        self.assertIn("governed native approval path", value)
        self.assertIn("AWS service verification", value)
        self.assertIn("AWS service readback", value)

    def test_invalid_request_fails_before_backend_read(self):
        with patch.object(agent, "current_evidence") as evidence:
            with self.assertRaisesRegex(ValueError, "user request is invalid"):
                agent.answer("   ", harness_arn="arn:any")
        evidence.assert_not_called()

    def test_max_request_and_bounded_identifiers_fit_harness_prompt(self):
        checks = []
        for alias in config_backend.ALIASES:
            for control in config_backend.CONTROLS:
                item = {
                    "account_alias": alias,
                    "control": control,
                    "status": "NON_COMPLIANT",
                    "affected_resources": 10,
                }
                item.update(config_backend._optional_identifiers({
                    "accountId": "123456789012",
                    "resourceId": "r" * config_backend.MAX_IDENTIFIER_CHARS,
                    "resourceIds": ["x" * config_backend.MAX_IDENTIFIER_CHARS] * 10,
                }))
                checks.append(item)
        evidence = {
            "version": 1,
            "source": "Unified Config backend",
            "fetched_at": "now",
            "aliases": list(config_backend.ALIASES),
            "controls": list(config_backend.CONTROLS),
            "checks": checks,
            "identifiers_available": True,
            "read_only": True,
        }
        prompt = agent.build_prompt("q" * 4000, evidence)
        self.assertLess(len(prompt), 24000)
        self.assertIn("resource_ids_truncated", prompt)


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
    def test_v1_integration_uses_clean_read_path_and_bounded_existing_executor(self):
        installer = (ROOT / "integration" / "install-compliance-v1.cjs").read_text()
        spec = json.loads((ROOT / "integration" / "compliance-agent-v1.json").read_text())
        self.assertEqual(spec["name"], "Compliance Agent v1")
        self.assertEqual(spec["conversation_starters"], ["Status", "Fix S3", "Fix SSH", "Verify latest"])
        self.assertLessEqual(len(spec["conversation_starters"]), 4)
        self.assertIn("| AWS Account | 🪣 S3 Block Public Access | 🛡️ Restricted SSH |", spec["instructions"])
        self.assertIn("✅ COMPLIANT", spec["instructions"])
        self.assertIn("❌ NON-COMPLIANT", spec["instructions"])
        self.assertIn("➡️ Next:", spec["instructions"])
        self.assertIn("AWS service verification", spec["instructions"])
        self.assertIn("AWS Config evaluation", spec["instructions"])
        self.assertIn("NATIVE APPROVAL HANDOFF (MANDATORY, OVERRIDES", spec["instructions"])
        self.assertIn("do not emit assistant text", spec["instructions"])
        self.assertIn("native Approve/Reject + Submit card", spec["instructions"])
        self.assertIn("RICH RESULTS", spec["instructions"])
        self.assertIn("UI Resource Marker", spec["instructions"])
        self.assertEqual(spec["tools"], [
            "ask_compliance_agent_v1_mcp_compliance_agent_v1",
            "prepare_multi_account_remediation_mcp_aws_compliance_planner",
            "execute_multi_account_remediation_mcp_aws_compliance_planner",
            "verify_multi_account_remediation_mcp_aws_compliance_planner",
        ])
        instructions = spec["instructions"]
        self.assertIn("READ / EXPLAIN / PLAN", instructions)
        self.assertIn("EXPLICIT FIX", instructions)
        self.assertIn("zero remediation execution dispatch and zero AWS resource writes", instructions)
        self.assertIn("two separate native approval decisions", instructions)
        self.assertIn("never combine them into Approve All", instructions)
        self.assertIn("Harness remains tool-free", instructions)
        self.assertNotIn("start_batch_execution_mcp_aws_secops_executor", json.dumps(spec))
        self.assertNotIn("start_sg_batch_execution_mcp_aws_compliance", json.dumps(spec))
        self.assertIn("CONFIG_BACKEND_URL:'http://127.0.0.1:1111'", installer)
        self.assertIn("pilot_v1.operator_mcp", installer)
        self.assertIn("SECOPS_OPERATOR_BACKEND_URL:'http://localhost:4444'", installer)
        self.assertIn("prepare_multi_account_remediation_mcp_aws_compliance_planner", installer)
        self.assertIn("execute_multi_account_remediation_mcp_aws_compliance_planner", installer)
        self.assertIn("verify_multi_account_remediation_mcp_aws_compliance_planner", installer)
        self.assertIn("multi-account-approval-hook.cjs", installer)
        self.assertIn("timeout:300000", installer)
        self.assertIn("four-account v1 execution must not be statically allowed", installer)
        self.assertIn("exclude_resources", instructions)
        self.assertIn("exact bucket names", instructions)
        self.assertIn("Never infer criticality", instructions)
        self.assertIn("scope_hash", instructions)
        self.assertIn("never pass a new/changed exclusion at execution time", instructions)
        self.assertIn("RECOVERED_VERIFIED", instructions)
        self.assertIn("do not retry mutation", instructions)
        self.assertIn("EXPLICIT FIX (HIGHEST PRECEDENCE)", instructions)
        self.assertIn("DO NOT call ask_compliance_agent_v1 first", instructions)
        self.assertIn("Call prepare_multi_account_remediation directly", instructions)
        self.assertIn("OMIT include_accounts", instructions)
        self.assertIn("Preparation itself performs the fresh four-account compliance read", instructions)
        self.assertIn("Never turn Fix S3/Fix SSH into a read-only Status response", instructions)
        self.assertIn("OVERRIDES ALL GENERAL NEXT/CONFIRMATION RULES", instructions)
        hook = (ROOT / "integration" / "multi-account-approval-hook.cjs").read_text()
        self.assertIn("excluded_resources", hook)
        self.assertIn("These excluded findings remain non-compliant", hook)
        self.assertIn("Allow Compliance Agent v1 to apply", hook)
        self.assertIn("Selected accounts:", hook)
        self.assertIn("Choose Approve or Reject, then Submit.", hook)
        self.assertIn("allowedDecisions: ['approve', 'reject']", hook)
        self.assertIn("Reject makes zero remediation execution dispatch and zero AWS resource writes.", hook)
        self.assertIn("APPROVAL_TTL_SECONDS = 1800", hook)
        self.assertIn("Approval is valid for 30 minutes from preparation.", hook)
        operator_server = (ROOT / "pilot_v1" / "operator_server.py").read_text()
        self.assertIn("APPROVAL_TTL_SECONDS = 1800", operator_server)
        self.assertIn("age > APPROVAL_TTL_SECONDS", operator_server)
        approval_patch = (ROOT / "integration" / "patch-librechat-approval-description.cjs").read_text()
        self.assertIn("output.allowedDecisions != null", approval_patch)
        self.assertIn("STATIC_ASK=PRESERVED", approval_patch)
        operator_mcp = (ROOT / "pilot_v1" / "operator_mcp.py").read_text()
        self.assertIn("exclude_resources: list[str] | None = None", operator_mcp)
        self.assertIn("execute exclusions are frozen server-side during prepare", operator_mcp)
        self.assertIn("include_accounts: list[str] | None = None", operator_mcp)
        self.assertIn("verify_multi_account_remediation", operator_mcp)
        self.assertIn('"mode": "IMMEDIATE_NATIVE_ASK"', operator_mcp)
        self.assertIn("Do not emit assistant text", operator_mcp)

    def test_v1_release_publisher_is_manual_main_only_and_immutable(self):
        workflow = (ROOT / ".github" / "workflows" / "publish-compliance-v1-release.yml").read_text()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertNotIn("push:", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn("contents: write", workflow)
        self.assertIn("compliance-agent-v1.0.0", workflow)
        self.assertIn('--target "$GITHUB_SHA"', workflow)
        self.assertIn("release tag already exists", workflow)
        self.assertIn("release already exists", workflow)
        self.assertIn('test "$tag_sha" = "$GITHUB_SHA"', workflow)

    def test_agent_updater_preserves_identity_and_exact_tools(self):
        updater = (ROOT / "integration" / "update-compliance-v1-agent.cjs").read_text()
        self.assertIn("expected exactly one existing Compliance Agent v1", updater)
        self.assertIn("after.id !== before.id", updater)
        self.assertIn("String(after.author) !== String(before.author)", updater)
        self.assertIn("toolCount !== 4", updater)
        self.assertIn("starterCount !== 4", updater)
        self.assertIn("conversation_starters: spec.conversation_starters", updater)
        self.assertIn("instructions: spec.instructions", updater)
        self.assertNotIn("fixEvidenceInstruction", updater)
        self.assertNotIn("pass that exact short command to ask_compliance_agent_v1", updater)
        staging = (ROOT / "scripts" / "prepare-sg-compliance.py").read_text()
        self.assertIn('"integration/update-compliance-v1-agent.cjs"', staging)
        self.assertIn('"integration/compliance-agent-v1.json"', staging)
        self.assertIn("update-compliance-v1-agent.cjs /opt/aws-secops/integration/compliance-agent-v1.json", staging)
        self.assertNotIn("insertOne", updater)
        self.assertNotIn("deleteOne", updater)

    def test_access_helper_is_bounded_and_idempotent(self):
        helper = (ROOT / "integration" / "ensure-compliance-v1-access.cjs").read_text()
        self.assertIn("AWS Compliance Agent", helper)
        self.assertIn("Compliance Agent v1", helper)
        self.assertIn("target user must already have source-agent access", helper)
        self.assertIn("conflicting target ACL; manual review required", helper)
        self.assertIn("countDocuments", helper)
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
        self.assertIn("read-only reasoning component behind Compliance Agent v1", template)
        self.assertIn("outer Compliance Agent may offer remediation", template)
        self.assertNotIn("say Compliance Agent v1 cannot execute changes", template)
        self.assertNotIn("4444", template)


if __name__ == "__main__":
    unittest.main()
