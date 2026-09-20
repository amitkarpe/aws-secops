import json
from pathlib import Path
import unittest
from unittest.mock import patch

from pilot_v1 import operator_mcp


class ComplianceAgentSpecTests(unittest.TestCase):
    def test_one_named_agent_has_both_exact_families(self):
        root = Path(__file__).resolve().parents[1]
        value = json.loads((root / "integration" / "compliance-agent.json").read_text())
        self.assertEqual(value["name"], "AWS Compliance Agent")
        tools = set(value["tools"])
        self.assertIn("start_batch_execution_mcp_aws_secops_executor", tools)
        self.assertIn("start_sg_batch_execution_mcp_aws_compliance", tools)
        self.assertIn("get_multi_account_status_mcp_aws_compliance", tools)
        self.assertIn("get_multi_account_remediation_plan_mcp_aws_compliance_planner", tools)
        self.assertIn("prepare_multi_account_remediation_mcp_aws_compliance_planner", tools)
        self.assertIn("execute_multi_account_remediation_mcp_aws_compliance_planner", tools)
        self.assertIn("get_config_summary_mcp_aws_compliance", tools)
        self.assertIn("list_config_findings_mcp_aws_compliance", tools)
        self.assertIn("list_batches_mcp_aws_secops_reader", tools)
        self.assertIn("list_sg_batches_mcp_aws_compliance", tools)
        self.assertIn("prepare_remediation_mcp_aws_compliance_planner", tools)
        self.assertNotIn("prepare_remediation_batch_mcp_aws_compliance_planner", tools)
        self.assertNotIn("prepare_eligible_remediation_batches_mcp_aws_compliance_planner", tools)
        instructions = value["instructions"]
        self.assertIn("Never combine S3 and SG into one approval", instructions)
        self.assertIn("SCOPE BOUNDARY", instructions)
        self.assertIn("OUT OF SCOPE", instructions)
        self.assertIn("prepare_multi_account_remediation", instructions)
        self.assertIn("execute_multi_account_remediation", instructions)
        self.assertIn("do not claim AgentCore Harness is used", instructions)
        self.assertIn("DEFAULT LIVE SCOPE", instructions)
        self.assertIn("Never substitute the legacy 100/10 executor for a four-account fix request", instructions)
        self.assertIn("Reject means zero CodeBuild dispatch", instructions)
        installer = (root / "integration" / "install-compliance.cjs").read_text()
        self.assertIn("'get_multi_account_status_mcp_aws_compliance'", installer)
        self.assertIn("'get_multi_account_remediation_plan_mcp_aws_compliance_planner'", installer)
        self.assertIn("'prepare_multi_account_remediation_mcp_aws_compliance_planner'", installer)
        self.assertIn("'execute_multi_account_remediation_mcp_aws_compliance_planner'", installer)
        self.assertIn("multi-account-approval-hook.cjs", installer)
        self.assertIn("const legacyPlanner =", installer)
        self.assertIn("timeout:95000", installer)
        self.assertIn("timeout:300000", installer)
        self.assertIn("'prepare_remediation_mcp_aws_compliance_planner'", installer)
        self.assertIn("retiredPlannerTools", installer)
        self.assertNotIn("WAF exact remediation", instructions)
        self.assertFalse((root / "pilot_v1" / "static" / "bulk-s3-demo.html").exists())


class PlannerTests(unittest.TestCase):
    def test_completed_s3_is_skipped_and_pending_sg_is_prepared(self):
        calls = []
        batch_id = "a" * 64

        def fake_call(operation, control):
            calls.append((operation, control))
            if (operation, control) == ("plan", "all"):
                return {
                    "version": 1,
                    "plans": [
                        {"control": operator_mcp.S3_CONTROL, "ready_to_prepare": False,
                         "current_batch": {"decision": "APPROVE", "verified": 100}},
                        {"control": operator_mcp.SG_CONTROL, "ready_to_prepare": True,
                         "current_batch": {"decision": "PENDING", "verified": 0}},
                    ],
                }
            if (operation, control) == ("prepare", operator_mcp.SG_CONTROL):
                return {"version": 1, "prepared": True,
                        "batch": {"batch_id": batch_id, "approval_hash": batch_id}}
            raise AssertionError(f"unexpected planner call: {operation} {control}")

        with patch.object(operator_mcp, "call", side_effect=fake_call):
            result = operator_mcp.prepare_eligible()

        self.assertEqual(calls, [("plan", "all"), ("prepare", operator_mcp.SG_CONTROL)])
        self.assertEqual(len(result["next_executions"]), 1)
        self.assertEqual(result["next_executions"][0]["tool"], "start_sg_batch_execution_mcp_aws_compliance")
        self.assertEqual(result["skipped"][0]["control"], operator_mcp.S3_CONTROL)
        self.assertEqual(result["skipped"][0]["reason"], "not_currently_eligible")

    def test_both_eligible_return_two_separate_executor_calls_in_order(self):
        calls = []
        ids = {operator_mcp.S3_CONTROL: "a" * 64, operator_mcp.SG_CONTROL: "b" * 64}

        def fake_call(operation, control):
            calls.append((operation, control))
            if (operation, control) == ("plan", "all"):
                return {
                    "version": 1,
                    "plans": [
                        {"control": operator_mcp.S3_CONTROL, "ready_to_prepare": True, "current_batch": {}},
                        {"control": operator_mcp.SG_CONTROL, "ready_to_prepare": True, "current_batch": {}},
                    ],
                }
            if operation == "prepare" and control in ids:
                return {"version": 1, "prepared": True,
                        "batch": {"batch_id": ids[control], "approval_hash": ids[control]}}
            raise AssertionError(f"unexpected planner call: {operation} {control}")

        with patch.object(operator_mcp, "call", side_effect=fake_call):
            result = operator_mcp.prepare_eligible()

        self.assertEqual([x["tool"] for x in result["next_executions"]], [
            "start_batch_execution_mcp_aws_secops_executor",
            "start_sg_batch_execution_mcp_aws_compliance",
        ])
        self.assertEqual(result["skipped"], [])
        self.assertEqual(calls, [
            ("plan", "all"),
            ("prepare", operator_mcp.S3_CONTROL),
            ("prepare", operator_mcp.SG_CONTROL),
        ])

    def test_single_family_prepare_uses_same_internal_entry(self):
        batch_id = "c" * 64
        with patch.object(operator_mcp, "call", return_value={
            "version": 1, "prepared": True,
            "batch": {"batch_id": batch_id, "approval_hash": batch_id},
        }) as mocked:
            result = operator_mcp.prepare_one(operator_mcp.S3_CONTROL)
        mocked.assert_called_once_with("prepare", operator_mcp.S3_CONTROL)
        self.assertEqual(result["next_execution"]["tool"], "start_batch_execution_mcp_aws_secops_executor")


if __name__ == "__main__":
    unittest.main()
