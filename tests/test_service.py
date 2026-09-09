import json
import unittest

from pilot_v1.config import PilotConfig
from pilot_v1.service import PilotService


FINDING = {
    "resource_id": "sg-private",
    "resource_name": "pilot-demo",
    "control": "TCP/22",
    "status": "NON_COMPLIANT",
    "source": "0.0.0.0/0",
    "recommendation": "Remove exact rule",
    "mutation": "none",
}


class ServiceTest(unittest.TestCase):
    def setUp(self):
        self.provider_status = "NON_COMPLIANT"

    def config(self, s3_tool=""):
        return PilotConfig(
            "ap-southeast-1",
            "model",
            "arn:harness",
            "https://demo.gateway.bedrock-agentcore."
            "ap-southeast-1.amazonaws.com",
            "read_tool",
            "remediate_tool",
            s3_tool,
        )

    def gateway(self, url, region, profile, tool, arguments):
        if tool == "read_tool":
            finding = dict(FINDING, status=self.provider_status)
            return {"result": {"isError": False, "content": [{"type": "text", "text": json.dumps(finding)}]}}
        self.provider_status = "COMPLIANT"
        return {"result": {"isError": False, "content": [{"type": "text", "text": json.dumps({"result": "SSH_RULE_REMOVED", "changed": True, "verification": "COMPLIANT"})}]}}

    def harness(self, config, prompt):
        return {"response": "Grounded explanation", "tool_calls": 1, "tool_results": [FINDING]}

    def test_reject_has_visible_no_call_audit(self):
        service = PilotService(self.config(), harness_call=self.harness, gateway_call=self.gateway)
        service.check()
        result = service.reject()
        self.assertEqual(result["stage"], "REJECTED")
        self.assertEqual(result["audit"]["policy_decision"], "NOT_CALLED")
        self.assertFalse(result["audit"]["changed"])

    def test_approve_has_complete_allow_audit(self):
        service = PilotService(self.config(), harness_call=self.harness, gateway_call=self.gateway)
        service.check()
        result = service.approve("dev")
        self.assertEqual(result["stage"], "COMPLETED")
        self.assertEqual(result["audit"]["policy_decision"], "ALLOW")
        self.assertEqual(result["audit"]["provider_verification"], "COMPLIANT")
        self.assertTrue(result["audit"]["changed"])

    def test_prod_approval_has_visible_deny_audit(self):
        def denied_gateway(url, region, profile, tool, arguments):
            if tool == "read_tool":
                return self.gateway(url, region, profile, tool, arguments)
            return {"error": {"code": -32002, "message": "Tool Execution Denied: denied by default"}}

        service = PilotService(self.config(), harness_call=self.harness, gateway_call=denied_gateway)
        service.check()
        result = service.approve("prod")
        self.assertEqual(result["stage"], "DENIED")
        self.assertEqual(result["audit"]["policy_decision"], "DENY")
        self.assertEqual(result["audit"]["provider_verification"], "NON_COMPLIANT")
        self.assertFalse(result["audit"]["changed"])

    def test_s3_baseline_is_read_only_and_cannot_enable_sg_approval(self):
        s3_finding = {
            "resource_name": "pilot-bucket",
            "control": "five-control S3 baseline",
            "status": "COMPLIANT",
            "source": "AWS S3 control-plane APIs",
            "recommendation": "No action required.",
            "controls": [{"name": str(i), "status": "PASS"} for i in range(5)],
        }

        def s3_harness(config, prompt):
            return {"response": "Five controls passed", "tool_calls": 1, "tool_results": [s3_finding]}

        service = PilotService(self.config("s3_tool"), harness_call=s3_harness, gateway_call=self.gateway)
        result = service.check_s3()
        self.assertEqual(result["stage"], "S3_BASELINE")
        self.assertEqual(result["audit"]["exact_tool"], "s3_tool")
        self.assertFalse(result["audit"]["changed"])
        with self.assertRaisesRegex(RuntimeError, "Security Group"):
            service.approve("dev")


if __name__ == "__main__":
    unittest.main()
