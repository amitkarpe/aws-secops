import json
import unittest

from pilot_v1.read_lambda import PUBLIC_IPV4
from pilot_v1.remediation_lambda import remove_unrestricted_ssh
from pilot_v1.workflow import approve_remediation, reject_remediation


class FakeEc2:
    def __init__(self):
        self.present = True
        self.describe_calls = 0
        self.revoke_calls = 0

    def describe_security_groups(self, *, GroupIds):
        self.describe_calls += 1
        permissions = []
        if self.present:
            permissions = [{
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": PUBLIC_IPV4}],
            }]
        return {"SecurityGroups": [{"GroupId": GroupIds[0], "IpPermissions": permissions}]}

    def revoke_security_group_ingress(self, *, GroupId, IpPermissions):
        self.revoke_calls += 1
        self.present = False


class RemediationTest(unittest.TestCase):
    def test_exact_remediation_changes_once_and_verifies(self):
        ec2 = FakeEc2()
        result = remove_unrestricted_ssh(ec2, "sg-demo")
        self.assertEqual(result["result"], "SSH_RULE_REMOVED")
        self.assertEqual(result["verification"], "COMPLIANT")
        self.assertEqual(ec2.revoke_calls, 1)
        self.assertEqual(ec2.describe_calls, 2)

    def test_already_compliant_is_noop(self):
        ec2 = FakeEc2()
        ec2.present = False
        result = remove_unrestricted_ssh(ec2, "sg-demo")
        self.assertEqual(result["result"], "ALREADY_COMPLIANT")
        self.assertFalse(result["changed"])
        self.assertEqual(ec2.revoke_calls, 0)

    def test_reject_never_calls_gateway(self):
        calls = []
        result = reject_remediation()
        self.assertEqual(calls, [])
        self.assertEqual(result["gateway_decision"], "NOT_CALLED")
        self.assertFalse(result["changed"])

    def test_synthetic_prod_denial_has_no_change(self):
        def deny(tool_name, arguments):
            return {
                "error": {
                    "code": -32002,
                    "message": "Tool Execution Denied: denied by default",
                }
            }

        result = approve_remediation("prod", "exact_tool", deny)
        self.assertEqual(result["gateway_decision"], "DENY")
        self.assertFalse(result["changed"])

    def test_dev_approval_requires_exact_success_payload(self):
        def allow(tool_name, arguments):
            self.assertEqual(arguments, {"environment": "dev", "approved": True})
            payload = {"result": "SSH_RULE_REMOVED", "changed": True, "verification": "COMPLIANT"}
            return {"result": {"isError": False, "content": [{"type": "text", "text": json.dumps(payload)}]}}

        result = approve_remediation("dev", "exact_tool", allow)
        self.assertEqual(result["gateway_decision"], "ALLOW")
        self.assertTrue(result["changed"])


if __name__ == "__main__":
    unittest.main()
