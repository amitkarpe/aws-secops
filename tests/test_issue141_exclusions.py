from __future__ import annotations

import unittest

from pilot_v1.operator_server import OperatorService, SG_CONTROL
from pilot_v1.operator_mcp import server


class Issue141ExceptionContractTests(unittest.TestCase):
    def test_exact_exclusion_input_is_bounded(self):
        self.assertEqual(
            OperatorService._normalize_exclusions(["bucket-a"]),
            ["bucket-a"],
        )
        for bad in (
            ["*"],
            ["bucket?"],
            ["bucket-a", "bucket-a"],
            ["a", "b", "c", "d"],
        ):
            with self.assertRaises(ValueError):
                OperatorService._normalize_exclusions(bad)

    def test_exception_metadata_requires_reason_and_is_one_time(self):
        value = OperatorService._normalize_exception_metadata(
            ["bucket-a"],
            "Temporary approved business exception",
            "RA-2026-001",
            "2099-12-31",
        )
        self.assertEqual(value["reason"], "Temporary approved business exception")
        self.assertEqual(value["reference"], "RA-2026-001")
        self.assertEqual(value["expires_at"], "2099-12-31")
        self.assertRegex(value["requested_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

        with self.assertRaises(ValueError):
            OperatorService._normalize_exception_metadata(["bucket-a"])
        with self.assertRaises(ValueError):
            OperatorService._normalize_exception_metadata(
                [], "reason without exclusion", None, None
            )
        with self.assertRaises(ValueError):
            OperatorService._normalize_exception_metadata(
                ["bucket-a"], "ok reason", None, "not-a-date"
            )

    def test_prepare_schema_accepts_exception_but_execute_cannot_edit_it(self):
        tools = {tool.name: tool for tool in server._tool_manager.list_tools()}
        prepare = tools["prepare_multi_account_remediation"].parameters
        execute = tools["execute_multi_account_remediation"].parameters

        prepare_props = prepare.get("properties", {})
        self.assertIn("exclude_resources", prepare_props)
        self.assertIn("exception_reason", prepare_props)
        self.assertIn("exception_reference", prepare_props)
        self.assertIn("exception_expires_at", prepare_props)

        execute_props = execute.get("properties", {})
        self.assertEqual(set(execute_props), {"control", "batch_id", "scope_hash"})
        self.assertNotIn("exclude_resources", execute_props)
        self.assertNotIn("exception_reason", execute_props)

    def test_execute_rejects_changed_scope_hash_before_dispatch(self):
        service = object.__new__(OperatorService)
        service.multi_account_execution_preview = lambda _control: {
            "batch_id": "a" * 20,
            "scope_hash": "b" * 24,
        }
        with self.assertRaisesRegex(ValueError, "does not match frozen plan"):
            service.execute_multi_account(SG_CONTROL, "a" * 20, "c" * 24)

    def test_approval_hook_requires_scope_hash_and_authenticated_context(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        hook = (root / "integration" / "multi-account-approval-hook.cjs").read_text()
        self.assertIn("batch_id,control,scope_hash", hook)
        self.assertIn("preview?.scope_hash !== args.scope_hash", hook)
        self.assertIn("context?.userId", hook)
        self.assertIn("zero remediation execution dispatch and zero AWS resource writes", hook)


if __name__ == "__main__":
    unittest.main()
