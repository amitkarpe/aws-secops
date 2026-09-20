from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "agents" / "compliance-agent-v1" / "src"
sys.path.insert(0, str(SRC))

from compliance_agent_v1 import mcp_server as read_mcp  # noqa: E402
from compliance_agent_v1.ui_cards import render_fleet_card  # noqa: E402
from pilot_v1 import operator_mcp  # noqa: E402
from pilot_v1.ui_cards import (  # noqa: E402
    render_execution_result,
    render_remediation_preview,
    render_verification_result,
    tool_result,
)

S3 = "s3-bucket-level-public-access-prohibited"
SSH = "restricted-ssh"
ALIASES = ["lab-dev", "lab-poc", "lab-qa", "lab-sec"]


def evidence():
    checks = []
    for alias in ALIASES:
        checks.extend([
            {
                "account_alias": alias,
                "control": S3,
                "status": "NON_COMPLIANT" if alias in {"lab-dev", "lab-poc"} else "COMPLIANT",
                "affected_resources": 1 if alias in {"lab-dev", "lab-poc"} else 0,
            },
            {
                "account_alias": alias,
                "control": SSH,
                "status": "NON_COMPLIANT",
                "affected_resources": 1,
            },
        ])
    return {
        "source": "Unified Config backend",
        "fetched_at": "2026-09-21T00:00:00Z",
        "aliases": ALIASES,
        "controls": [S3, SSH],
        "check_count": 8,
        "checks": checks,
        "identifiers_available": False,
    }


class Issue155RichResultTests(unittest.TestCase):
    def test_fleet_card_is_glanceable_and_deterministic(self):
        html = render_fleet_card(evidence())
        self.assertIn("AWS Compliance", html)
        self.assertIn("🪣 S3 Block Public Access", html)
        self.assertIn("🛡️ Restricted SSH", html)
        self.assertIn("✅ COMPLIANT", html)
        self.assertIn("❌ NON-COMPLIANT", html)
        self.assertIn("Fix S3", html)
        self.assertNotIn("<script", html.lower())
        self.assertNotIn("account_id", html)

    def test_read_tool_returns_ui_resource_plus_exact_machine_payload(self):
        value = {
            "version": 1,
            "agent": "Compliance Agent v1",
            "runtime": "Amazon Bedrock AgentCore Harness",
            "answer": "Grounded answer",
            "evidence": evidence(),
            "mutation": False,
        }
        with patch.object(read_mcp, "answer", return_value=value):
            result = read_mcp.ask_compliance_agent_v1("Status")
        self.assertEqual(result.structuredContent, value)
        resources = [x.resource for x in result.content if getattr(x, "type", None) == "resource"]
        self.assertEqual(len(resources), 1)
        self.assertEqual(str(resources[0].uri), "ui://compliance-agent-v1/fleet-status")
        self.assertEqual(resources[0].mimeType, "text/html")

    def test_fix_intent_read_does_not_add_status_card_before_approval_flow(self):
        value = {
            "version": 1,
            "agent": "Compliance Agent v1",
            "runtime": "Amazon Bedrock AgentCore Harness",
            "answer": "Use governed native approval.",
            "evidence": evidence(),
            "mutation": False,
        }
        with patch.object(read_mcp, "answer", return_value=value):
            result = read_mcp.ask_compliance_agent_v1("Fix S3 in lab-dev")
        self.assertFalse(any(getattr(x, "type", None) == "resource" for x in result.content))

    def test_preview_card_hides_ids_under_technical_details(self):
        value = {
            "control": S3,
            "batch_id": "a" * 20,
            "scope_hash": "b" * 24,
            "selected_accounts": ["lab-dev", "lab-poc"],
            "unselected_accounts": ["lab-qa", "lab-sec"],
            "pending_aliases": ["lab-dev", "lab-poc"],
            "excluded_aliases": [],
            "excluded_resources": [],
            "exception": None,
        }
        html = render_remediation_preview(value)
        self.assertIn("Human approval required", html)
        self.assertIn("Reject + Submit performs zero remediation writes", html)
        self.assertIn("<details>", html)
        self.assertGreater(html.index("<details>"), html.index("Human approval required"))
        self.assertIn("a" * 20, html)
        self.assertIn("b" * 24, html)
        self.assertNotIn("<script", html.lower())

    def test_execution_and_verification_cards_use_simple_english(self):
        execution = {
            "control": S3,
            "batch_id": "a" * 20,
            "scope_hash": "b" * 24,
            "selected_accounts": ["lab-dev", "lab-poc"],
            "excluded_aliases": [],
            "included_aliases": ["lab-dev", "lab-poc"],
            "mutation_count": 2,
            "decision": "APPLIED_PENDING_VERIFICATION",
            "aws_change_applied": True,
            "aws_service_verification": "PENDING",
            "aws_config_evaluation": "PENDING",
        }
        html = render_execution_result(execution)
        self.assertIn("AWS change applied", html)
        self.assertIn("AWS service verification", html)
        self.assertIn("AWS Config evaluation", html)
        self.assertIn("Verify latest", html)
        self.assertNotIn("provider", html.lower())

        verification = {
            "control": S3,
            "selected_accounts": ["lab-dev", "lab-poc"],
            "aws_service_verification": "VERIFIED",
            "aws_config_evaluation": {"lab-dev": "COMPLIANT", "lab-poc": "PENDING"},
        }
        verify_html = render_verification_result(verification)
        self.assertIn("✅ VERIFIED", verify_html)
        self.assertIn("AWS Config evaluation", verify_html)
        self.assertIn("lab-dev", verify_html)
        self.assertIn("lab-poc", verify_html)

    def test_tool_result_preserves_structured_content_and_html_resource(self):
        value = {"version": 1, "control": S3, "batch_id": "a" * 20}
        result = tool_result(value, uri="ui://aws-secops/test", html="<section>safe</section>")
        self.assertEqual(result.structuredContent, value)
        self.assertEqual(result.content[0].type, "text")
        self.assertEqual(result.content[1].type, "resource")
        self.assertEqual(result.content[1].resource.mimeType, "text/html")

    def test_prepare_tool_returns_ui_resource_without_changing_native_ask_contract(self):
        frozen = {
            "version": 1,
            "control": S3,
            "batch_id": "a" * 20,
            "scope_hash": "b" * 24,
            "selected_accounts": ["lab-dev"],
            "unselected_accounts": ["lab-poc", "lab-qa", "lab-sec"],
            "pending_aliases": ["lab-dev"],
            "excluded_aliases": [],
            "excluded_resources": [],
            "exception": None,
            "next_execution": {
                "tool": "execute_multi_account_remediation_mcp_aws_compliance_planner",
                "arguments": {"control": S3, "batch_id": "a" * 20, "scope_hash": "b" * 24},
            },
        }
        with patch.object(operator_mcp, "multi_account_call", return_value=frozen):
            result = operator_mcp.prepare_multi_account_remediation(S3, include_accounts=["lab-dev"])
        self.assertEqual(result.structuredContent["assistant_transition"]["mode"], "IMMEDIATE_NATIVE_ASK")
        resources = [x for x in result.content if getattr(x, "type", None) == "resource"]
        self.assertEqual(len(resources), 1)
        self.assertTrue(str(resources[0].resource.uri).startswith("ui://aws-secops/remediation-preview/"))


if __name__ == "__main__":
    unittest.main()
