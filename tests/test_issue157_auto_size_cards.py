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
from pilot_v1.ui_cards import (  # noqa: E402
    render_execution_result,
    render_remediation_preview,
    render_verification_result,
    tool_result,
)

S3 = "s3-bucket-level-public-access-prohibited"
SSH = "restricted-ssh"
ALIASES = ["lab-dev", "lab-poc", "lab-qa", "lab-sec"]
FORBIDDEN_SCRIPT_APIS = ("fetch(", "XMLHttpRequest", "WebSocket", "localStorage", "sessionStorage", "location=", "window.open")


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


def assert_resize_bootstrap(testcase: unittest.TestCase, html: str) -> None:
    testcase.assertEqual(html.count("<script>"), 1)
    testcase.assertEqual(html.count("</script>"), 1)
    testcase.assertIn('"ui-size-change"', html)
    testcase.assertIn("ResizeObserver", html)
    testcase.assertIn("requestAnimationFrame", html)
    testcase.assertIn("Math.min(Math.max(natural+4,260),720)", html)
    testcase.assertIn('payload:{height}', html)
    testcase.assertNotIn("clientWidth", html)
    testcase.assertNotIn("payload:{width,height}", html)
    for token in FORBIDDEN_SCRIPT_APIS:
        testcase.assertNotIn(token, html)


class Issue157AutoSizeCardTests(unittest.TestCase):
    def test_all_rich_cards_share_bounded_resize_contract(self):
        status = render_fleet_card(evidence())
        preview = render_remediation_preview({
            "control": S3,
            "batch_id": "a" * 20,
            "scope_hash": "b" * 24,
            "selected_accounts": ["lab-dev", "lab-poc"],
            "unselected_accounts": ["lab-qa", "lab-sec"],
            "pending_aliases": ["lab-dev", "lab-poc"],
            "excluded_aliases": [],
            "excluded_resources": [],
            "exception": None,
        })
        execution = render_execution_result({
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
        })
        verification = render_verification_result({
            "control": S3,
            "batch_id": "a" * 20,
            "scope_hash": "b" * 24,
            "selected_accounts": ["lab-dev", "lab-poc"],
            "aws_service_verification": "VERIFIED",
            "aws_config_evaluation": {"lab-dev": "COMPLIANT", "lab-poc": "PENDING"},
        })
        for html in (status, preview, execution, verification):
            assert_resize_bootstrap(self, html)

    def test_dynamic_values_are_escaped_even_with_resize_script(self):
        ev = evidence()
        ev["fetched_at"] = '<img src=x onerror="alert(1)">'
        html = render_fleet_card(ev)
        self.assertNotIn('<img src=x onerror="alert(1)">', html)
        self.assertIn("&lt;img", html)
        assert_resize_bootstrap(self, html)

        preview = render_remediation_preview({
            "control": S3,
            "batch_id": "a" * 20,
            "scope_hash": "b" * 24,
            "selected_accounts": ["lab-dev"],
            "unselected_accounts": ["lab-poc", "lab-qa", "lab-sec"],
            "pending_aliases": ["lab-dev"],
            "excluded_aliases": ["lab-poc"],
            "excluded_resources": ['bucket-<script>alert(1)</script>'],
            "exception": {"reason": '<svg onload="alert(1)">'},
        })
        self.assertNotIn("bucket-<script>alert(1)</script>", preview)
        self.assertNotIn('<svg onload="alert(1)">', preview)
        self.assertIn("&lt;script&gt;", preview)
        self.assertIn("&lt;svg", preview)
        assert_resize_bootstrap(self, preview)

    def test_status_tool_text_tells_model_not_to_duplicate_table(self):
        value = {
            "version": 1,
            "agent": "Compliance Agent v1",
            "runtime": "Amazon Bedrock AgentCore Harness",
            "answer": "Long grounded answer that should not be copied for Status.",
            "evidence": evidence(),
            "mutation": False,
        }
        with patch.object(read_mcp, "answer", return_value=value):
            result = read_mcp.ask_compliance_agent_v1("Status")
        text = result.content[0].text
        self.assertIn("do not repeat the status as Markdown", text)
        self.assertIn("➡️ Next: Fix S3", text)
        self.assertNotIn("Long grounded answer", text)
        self.assertNotIn("| AWS Account |", text)
        self.assertEqual(result.structuredContent, value)

    def test_non_status_read_keeps_grounded_payload(self):
        value = {
            "version": 1,
            "agent": "Compliance Agent v1",
            "runtime": "Amazon Bedrock AgentCore Harness",
            "answer": "Grounded explanation",
            "evidence": evidence(),
            "mutation": False,
        }
        with patch.object(read_mcp, "answer", return_value=value):
            result = read_mcp.ask_compliance_agent_v1("Explain what needs attention")
        self.assertIn("Grounded explanation", result.content[0].text)

    def test_tool_result_can_use_concise_model_text_without_losing_structured_data(self):
        value = {"version": 1, "control": S3, "batch_id": "a" * 20}
        result = tool_result(
            value,
            uri="ui://aws-secops/result/test",
            html="<section>safe</section>",
            model_text="Render the native card once.",
        )
        self.assertEqual(result.content[0].text, "Render the native card once.")
        self.assertEqual(result.structuredContent, value)


if __name__ == "__main__":
    unittest.main()
