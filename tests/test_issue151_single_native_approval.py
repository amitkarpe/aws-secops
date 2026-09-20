from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from pilot_v1 import operator_mcp
from pilot_v1.multi_account_campaign import SG_CONTROL


ROOT = Path(__file__).resolve().parents[1]


class Issue151SingleNativeApprovalTests(unittest.TestCase):
    def test_prepare_returns_immediate_native_ask_transition(self):
        frozen = {
            "version": 1,
            "control": SG_CONTROL,
            "batch_id": "a" * 20,
            "scope_hash": "b" * 24,
            "next_execution": {
                "tool": "execute_multi_account_remediation_mcp_aws_compliance_planner",
                "arguments": {
                    "control": SG_CONTROL,
                    "batch_id": "a" * 20,
                    "scope_hash": "b" * 24,
                },
            },
        }
        with patch.object(operator_mcp, "multi_account_call", return_value=frozen):
            result = operator_mcp.prepare_multi_account_remediation(
                SG_CONTROL,
                include_accounts=["lab-dev"],
            )

        payload = result.structuredContent
        transition = payload["assistant_transition"]
        self.assertEqual(transition["mode"], "IMMEDIATE_NATIVE_ASK")
        self.assertIn("Do not emit assistant text", transition["instruction"])
        self.assertIn("native Approve/Reject + Submit card", transition["instruction"])
        self.assertEqual(payload["next_execution"], frozen["next_execution"])

    def test_chat_words_never_become_authorization_contract(self):
        planner_instructions = operator_mcp.server.instructions
        self.assertIn("native Approve/Reject card", planner_instructions)
        self.assertIn("never ask the user to type Approve, Reject, go, or yes", planner_instructions)
        execute = {
            tool.name: tool for tool in operator_mcp.server._tool_manager.list_tools()
        }["execute_multi_account_remediation"]
        self.assertEqual(
            set(execute.parameters.get("properties", {})),
            {"control", "batch_id", "scope_hash"},
        )

        agent_spec = json.loads((ROOT / "integration" / "compliance-agent-v1.json").read_text())
        agent_instructions = agent_spec["instructions"]
        self.assertIn("EXPLICIT FIX (HIGHEST PRECEDENCE)", agent_instructions)
        self.assertIn("never omit include_accounts for a generic Fix S3/Fix SSH request", agent_instructions)
        self.assertIn("A bare 'go' or 'yes' may continue only", agent_instructions)
        self.assertIn("Never use typed 'approve', 'reject', 'yes', or 'go' to start, continue, or authorize remediation.", agent_instructions)
        self.assertIn("OVERRIDES ALL GENERAL NEXT/CONFIRMATION RULES", agent_instructions)


if __name__ == "__main__":
    unittest.main()
