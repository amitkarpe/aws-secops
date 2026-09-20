from __future__ import annotations

import unittest

from pilot_v1.operator_server import OperatorService
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
        self.assertEqual(set(execute_props), {"control", "batch_id"})
        self.assertNotIn("exclude_resources", execute_props)
        self.assertNotIn("exception_reason", execute_props)


if __name__ == "__main__":
    unittest.main()
