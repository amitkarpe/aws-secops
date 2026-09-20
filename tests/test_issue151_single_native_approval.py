from __future__ import annotations

import unittest
from unittest.mock import patch

from pilot_v1 import operator_mcp
from pilot_v1.multi_account_campaign import SG_CONTROL


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

        transition = result["assistant_transition"]
        self.assertEqual(transition["mode"], "IMMEDIATE_NATIVE_ASK")
        self.assertIn("Do not emit assistant text", transition["instruction"])
        self.assertIn("native Approve/Reject + Submit card", transition["instruction"])
        self.assertEqual(result["next_execution"], frozen["next_execution"])

    def test_chat_words_never_become_authorization_contract(self):
        spec = operator_mcp.server.instructions
        self.assertIn("native Approve/Reject card", spec)
        execute = {
            tool.name: tool for tool in operator_mcp.server._tool_manager.list_tools()
        }["execute_multi_account_remediation"]
        self.assertEqual(
            set(execute.parameters.get("properties", {})),
            {"control", "batch_id", "scope_hash"},
        )


if __name__ == "__main__":
    unittest.main()
