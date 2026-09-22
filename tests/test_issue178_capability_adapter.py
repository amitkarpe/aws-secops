from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "agents" / "compliance-agent-v1" / "src"
sys.path.insert(0, str(SRC))

from compliance_agent_v1 import agent, capability_adapter, mcp_server  # noqa: E402
from compliance_agent_v1.ui_cards import render_capability_card  # noqa: E402


CONTRACT = SRC / "compliance_agent_v1" / "capabilities.public.json"
SCHEMA = ROOT / "agents" / "compliance-agent-v1" / "capability.schema.json"


def payload():
    return json.loads(CONTRACT.read_text())


def evidence():
    return {
        "version": 1,
        "source": "Unified Config backend",
        "fetched_at": "2026-09-22T12:00:00Z",
        "aliases": ["lab-dev", "lab-poc", "lab-qa", "lab-sec"],
        "controls": ["s3-bucket-level-public-access-prohibited", "restricted-ssh"],
        "checks": [],
        "identifiers_available": False,
        "diagnostics": {"config_provider": "READY"},
        "read_only": True,
    }


class CapabilityAdapterTests(unittest.TestCase):
    def test_default_contract_is_deterministic_and_public_safe(self):
        summary = capability_adapter.CapabilityCatalog(payload()).summary()
        self.assertEqual(
            [row["control_key"] for row in summary["controls"]],
            ["restricted_ssh", "s3_backup", "s3_logging", "s3_ssl"],
        )
        self.assertEqual(summary["controls"][0]["capability_state"], "VERIFY")
        self.assertTrue(summary["controls"][0]["requires_human_approval"])
        self.assertEqual(
            {row["capability_state"] for row in summary["controls"][1:]}, {"EXPLAIN"}
        )
        self.assertTrue(summary["read_only"])
        self.assertFalse(summary["execution_authorized"])
        serialized = json.dumps(summary, sort_keys=True)
        for forbidden in ("rule_id", "account_id", "owner", "source_path", "finding"):
            self.assertNotIn(forbidden, serialized.lower())

    def test_unknown_and_private_fields_fail_closed(self):
        for location, key in (("top", "private_catalog"), ("record", "internal_rule_id")):
            value = payload()
            if location == "top":
                value[key] = "private"
            else:
                value["capabilities"][0][key] = "private"
            with self.subTest(location=location):
                with self.assertRaises(capability_adapter.CapabilityContractError):
                    capability_adapter.CapabilityCatalog(value)

    def test_malformed_and_unknown_controls_fail_closed(self):
        missing = payload()
        missing["capabilities"].pop()
        with self.assertRaisesRegex(capability_adapter.CapabilityContractError, "exactly four"):
            capability_adapter.CapabilityCatalog(missing)

        unknown = payload()
        unknown["capabilities"][0]["control_key"] = "private_control"
        with self.assertRaisesRegex(capability_adapter.CapabilityContractError, "outside"):
            capability_adapter.CapabilityCatalog(unknown)

    def test_over_privileged_control_and_missing_approval_are_rejected(self):
        over = payload()
        row = next(item for item in over["capabilities"] if item["control_key"] == "s3_ssl")
        row.update({
            "capability_state": "REMEDIATE",
            "supports_prepare": True,
            "supports_remediate": True,
            "requires_human_approval": True,
            "provider_verification_required": True,
        })
        with self.assertRaises(capability_adapter.CapabilityContractError):
            capability_adapter.CapabilityCatalog(over)

        no_approval = payload()
        ssh = next(item for item in no_approval["capabilities"] if item["control_key"] == "restricted_ssh")
        ssh["requires_human_approval"] = False
        with self.assertRaisesRegex(capability_adapter.CapabilityContractError, "human approval"):
            capability_adapter.CapabilityCatalog(no_approval)

    def test_decision_never_authorizes_execution(self):
        catalog = capability_adapter.CapabilityCatalog(payload())
        remediation = catalog.decision("restricted_ssh", "REMEDIATE")
        self.assertTrue(remediation["supported"])
        self.assertEqual(remediation["route"], "existing-governed-path")
        self.assertTrue(remediation["requires_human_approval"])
        self.assertFalse(remediation["execution_authorized"])

        unsupported = catalog.decision("private_control", "REMEDIATE")
        self.assertEqual(unsupported["control_key"], "unsupported")
        self.assertFalse(unsupported["supported"])
        self.assertEqual(unsupported["route"], "read-only-unsupported")
        self.assertNotIn("private_control", json.dumps(unsupported))

        s3 = catalog.decision("s3_ssl", "REMEDIATE")
        self.assertFalse(s3["supported"])
        self.assertEqual(s3["route"], "read-only")
        self.assertFalse(s3["execution_authorized"])

    def test_schema_is_closed_and_matches_public_registry(self):
        schema = json.loads(SCHEMA.read_text())
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(schema["$defs"]["capability"]["additionalProperties"])
        keys = set(schema["$defs"]["capability"]["properties"]["control_key"]["enum"])
        self.assertEqual(keys, set(capability_adapter.APPROVED_CONTROLS))

    def test_agent_receives_capability_metadata_without_new_execution_authority(self):
        def fake(prompt, _arn, region):
            self.assertIn('"capability_catalog"', prompt)
            self.assertIn("Capability metadata never authorizes", prompt)
            self.assertEqual(region, "ap-southeast-1")
            return {"answer": "Capability summary"}

        with patch.object(agent, "current_evidence", return_value=evidence()):
            result = agent.answer("Show capabilities", harness_arn="arn:any", harness_call=fake)
        self.assertEqual(len(result["capabilities"]["controls"]), 4)
        self.assertFalse(result["capabilities"]["execution_authorized"])
        self.assertFalse(result["mutation"])

    def test_capability_packet_keeps_maximum_prompt_bounded(self):
        captured = {}

        def fake(prompt, _arn, region):
            captured["prompt"] = prompt
            self.assertEqual(region, "ap-southeast-1")
            return {"answer": "Bounded"}

        large = evidence()
        large["checks"] = [
            {
                "account_alias": alias,
                "control": control,
                "status": "NON_COMPLIANT",
                "affected_resources": 10,
                "resource_ids": ["x" * 128] * 4,
            }
            for alias in large["aliases"]
            for control in large["controls"]
        ]
        with patch.object(agent, "current_evidence", return_value=large):
            agent.answer("q" * 4000, harness_arn="arn:any", harness_call=fake)
        self.assertLess(len(captured["prompt"]), 26000)

    def test_capability_card_is_compact_and_drops_unrecognized_metadata(self):
        summary = capability_adapter.current_capabilities()
        summary["controls"][0]["internal_rule_id"] = "must-not-render"
        html = render_capability_card(summary)
        self.assertIn("Compliance capabilities", html)
        self.assertIn("s3_ssl", html)
        self.assertIn("restricted_ssh", html)
        self.assertIn("no execution authorization", html)
        self.assertNotIn("must-not-render", html)
        self.assertEqual(html.lower().count("<script"), 1)

    def test_mcp_capability_request_returns_only_capability_card(self):
        value = {
            "version": 1,
            "agent": "Compliance Agent v1",
            "runtime": "Amazon Bedrock AgentCore Harness",
            "answer": "Capability summary",
            "capabilities": capability_adapter.current_capabilities(),
            "evidence": evidence(),
            "mutation": False,
        }
        with patch.object(mcp_server, "answer", return_value=value):
            result = mcp_server.ask_compliance_agent_v1("Show capability support")
        resources = [item.resource for item in result.content if item.type == "resource"]
        self.assertEqual(len(resources), 1)
        self.assertEqual(str(resources[0].uri), "ui://compliance-agent-v1/capabilities")
        self.assertEqual(result.structuredContent, value)

        with patch.object(mcp_server, "answer", return_value=value):
            status_result = mcp_server.ask_compliance_agent_v1("Capability status for s3 ssl")
        self.assertIn("Capability summary", status_result.content[0].text)
        self.assertNotIn("fleet status", status_result.content[0].text)

    def test_integration_instructions_do_not_route_new_s3_keys_to_executor(self):
        integration = json.loads((ROOT / "integration" / "compliance-agent-v1.json").read_text())
        instructions = integration["instructions"]
        self.assertIn("SANITIZED CAPABILITY BOUNDARY", instructions)
        self.assertIn("s3_ssl, s3_logging and s3_backup", instructions)
        self.assertIn("must never be routed to the S3 Block Public Access planner", instructions)
        self.assertIn("Capability metadata and typed chat approval never authorize execution", instructions)
        self.assertEqual(len(integration["tools"]), 4)


if __name__ == "__main__":
    unittest.main()
