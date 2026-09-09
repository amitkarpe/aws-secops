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

    def config(self):
        return PilotConfig(
            "ap-southeast-1",
            "model",
            "arn:harness",
            "https://demo.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com",
            "read_tool",
            "remediate_tool",
            "",
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


if __name__ == "__main__":
    unittest.main()
