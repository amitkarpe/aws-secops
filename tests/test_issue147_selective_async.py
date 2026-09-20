from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from pilot_v1.multi_account_campaign import SG_CONTROL
from pilot_v1.operator_mcp import server
from pilot_v1.operator_server import OperatorService


class Issue147SelectiveAsyncTests(unittest.TestCase):
    def test_selected_account_normalizer(self):
        self.assertEqual(
            OperatorService._normalize_selected_accounts(["lab-dev", "lab-poc"]),
            ["lab-dev", "lab-poc"],
        )
        self.assertEqual(
            OperatorService._normalize_selected_accounts(None),
            ["lab-dev", "lab-poc", "lab-qa", "lab-sec"],
        )
        for bad in (
            [],
            ["lab-poc", "lab-dev"],
            ["lab-dev", "lab-dev"],
            ["prod"],
        ):
            with self.assertRaises(ValueError):
                OperatorService._normalize_selected_accounts(bad)

    def test_prepare_tool_accepts_selected_accounts_and_verify_tool_is_read_only(self):
        tools = {tool.name: tool for tool in server._tool_manager.list_tools()}
        prepare = tools["prepare_multi_account_remediation"].parameters
        verify = tools["verify_multi_account_remediation"].parameters
        self.assertIn("include_accounts", prepare.get("properties", {}))
        self.assertEqual(set(verify.get("properties", {})), {"control"})

    def test_prepare_freezes_only_selected_scope(self):
        service = object.__new__(OperatorService)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        service.execution_state = Path(tmp.name) / "execution.json"
        service.multi_account_status = lambda: {
            "accounts": [
                {"alias": "lab-dev", "controls": {SG_CONTROL: "NON_COMPLIANT"}},
                {"alias": "lab-poc", "controls": {SG_CONTROL: "NON_COMPLIANT"}},
                {"alias": "lab-qa", "controls": {SG_CONTROL: "COMPLIANT"}},
                {"alias": "lab-sec", "controls": {SG_CONTROL: "COMPLIANT"}},
            ]
        }
        fake_plan = {
            "decision": "PLAN",
            "batch_id": "a" * 20,
            "pending_aliases": ["lab-dev", "lab-poc"],
            "excluded_aliases": [],
            "excluded_count": 0,
        }
        with patch("pilot_v1.operator_server.run_four_account_build", return_value=fake_plan) as run:
            value = service.prepare_multi_account_execution(
                SG_CONTROL,
                ["lab-dev", "lab-poc"],
            )
        self.assertEqual(value["selected_accounts"], ["lab-dev", "lab-poc"])
        self.assertEqual(value["unselected_accounts"], ["lab-qa", "lab-sec"])
        self.assertEqual(value["pending_aliases"], ["lab-dev", "lab-poc"])
        self.assertFalse(value["mutation"])
        saved = json.loads(service.execution_state.read_text())["plans"][SG_CONTROL]
        self.assertEqual(saved["selected_accounts"], ["lab-dev", "lab-poc"])
        self.assertEqual(saved["unselected_accounts"], ["lab-qa", "lab-sec"])
        self.assertEqual(run.call_args.kwargs["include_accounts"], ["lab-dev", "lab-poc"])

    def test_execute_returns_verification_pending_without_readback_requirement(self):
        service = object.__new__(OperatorService)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        service.execution_state = Path(tmp.name) / "execution.json"
        service.execution_state.write_text(json.dumps({
            "version": 1,
            "plans": {
                SG_CONTROL: {
                    "control": SG_CONTROL,
                    "batch_id": "a" * 20,
                    "selected_accounts": ["lab-dev", "lab-poc"],
                    "unselected_accounts": ["lab-qa", "lab-sec"],
                    "pending_aliases": ["lab-dev", "lab-poc"],
                    "excluded_aliases": [],
                    "exclude_resources": [],
                    "exception": {"reason": None, "reference": None, "expires_at": None, "requested_at": None},
                    "scope_hash": "b" * 24,
                    "created_at": int(time.time()),
                    "execution_state": "PENDING_APPROVAL",
                }
            },
        }))
        service.multi_account_status = lambda: {
            "accounts": [
                {"alias": "lab-dev", "controls": {SG_CONTROL: "NON_COMPLIANT"}},
                {"alias": "lab-poc", "controls": {SG_CONTROL: "NON_COMPLIANT"}},
                {"alias": "lab-qa", "controls": {SG_CONTROL: "COMPLIANT"}},
                {"alias": "lab-sec", "controls": {SG_CONTROL: "COMPLIANT"}},
            ]
        }
        result = {
            "decision": "APPROVE",
            "mutation_count": 2,
            "provider_verified": False,
            "included_aliases": ["lab-dev", "lab-poc"],
            "excluded_aliases": [],
            "config": {"lab-dev": "NON_COMPLIANT", "lab-poc": "NON_COMPLIANT"},
        }
        with patch("pilot_v1.operator_server.run_four_account_build", return_value=result) as run:
            value = service.execute_multi_account(SG_CONTROL, "a" * 20, "b" * 24)
        self.assertEqual(value["decision"], "APPLIED_PENDING_VERIFICATION")
        self.assertTrue(value["aws_change_applied"])
        self.assertEqual(value["aws_service_verification"], "PENDING")
        self.assertEqual(value["aws_config_evaluation"], "PENDING")
        self.assertEqual(run.call_args.kwargs["include_accounts"], ["lab-dev", "lab-poc"])
        saved = json.loads(service.execution_state.read_text())["plans"][SG_CONTROL]
        self.assertEqual(saved["execution_state"], "APPLIED_PENDING_VERIFICATION")

    def test_verify_is_read_only_and_updates_state(self):
        service = object.__new__(OperatorService)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        service.execution_state = Path(tmp.name) / "execution.json"
        service.execution_state.write_text(json.dumps({
            "version": 1,
            "plans": {
                SG_CONTROL: {
                    "control": SG_CONTROL,
                    "batch_id": "a" * 20,
                    "selected_accounts": ["lab-dev", "lab-poc"],
                    "unselected_accounts": ["lab-qa", "lab-sec"],
                    "pending_aliases": ["lab-dev", "lab-poc"],
                    "excluded_aliases": [],
                    "exclude_resources": [],
                    "scope_hash": "b" * 24,
                    "created_at": int(time.time()),
                    "execution_state": "APPLIED_PENDING_VERIFICATION",
                }
            },
        }))
        verified = {
            "aws_service_verification": "VERIFIED",
            "included_aliases": ["lab-dev", "lab-poc"],
            "excluded_aliases": [],
            "config": {"lab-dev": "PENDING", "lab-poc": "COMPLIANT"},
        }
        with patch("pilot_v1.operator_server.run_four_account_build", return_value=verified) as run:
            value = service.verify_multi_account_execution(SG_CONTROL)
        self.assertTrue(value["verified"])
        self.assertEqual(value["aws_service_verification"], "VERIFIED")
        self.assertEqual(value["aws_config_evaluation"]["lab-dev"], "PENDING")
        self.assertEqual(run.call_args.args[0], "verify")
        saved = json.loads(service.execution_state.read_text())["plans"][SG_CONTROL]
        self.assertEqual(saved["execution_state"], "VERIFIED")


if __name__ == "__main__":
    unittest.main()
