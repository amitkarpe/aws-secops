import json
from pathlib import Path
import unittest


class ComplianceAgentSpecTests(unittest.TestCase):
    def test_one_named_agent_has_both_exact_families(self):
        root = Path(__file__).resolve().parents[1]
        value = json.loads((root / "integration" / "compliance-agent.json").read_text())
        self.assertEqual(value["name"], "AWS Compliance Agent")
        tools = set(value["tools"])
        self.assertIn("start_batch_execution_mcp_aws_secops_executor", tools)
        self.assertIn("start_sg_batch_execution_mcp_aws_compliance", tools)
        self.assertIn("get_config_summary_mcp_aws_compliance", tools)
        self.assertIn("list_config_findings_mcp_aws_compliance", tools)
        self.assertIn("list_batches_mcp_aws_secops_reader", tools)
        self.assertIn("list_sg_batches_mcp_aws_compliance", tools)
        instructions = value["instructions"]
        self.assertIn("Never combine S3 and SG into one approval", instructions)
        self.assertIn("FIX-ALL CONTINUATION", instructions)
        self.assertIn("S3 first, then SG", instructions)
        self.assertIn("Never require another user message", instructions)
        planner = (root / "pilot_v1" / "operator_mcp.py").read_text()
        self.assertIn("keep that fix-all intent active across the native ASK pause", planner)
        self.assertNotIn("WAF exact remediation", instructions)
        self.assertFalse((root / "pilot_v1" / "static" / "bulk-s3-demo.html").exists())


if __name__ == "__main__":
    unittest.main()
