import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pilot_v1.read_lambda import PUBLIC_IPV4, check_security_group, lambda_handler


class FakeEc2:
    def __init__(self, permissions):
        self.permissions = permissions
        self.calls = 0

    def describe_security_groups(self, *, GroupIds):
        self.calls += 1
        return {
            "SecurityGroups": [
                {
                    "GroupId": GroupIds[0],
                    "GroupName": "pilot-demo",
                    "IpPermissions": self.permissions,
                }
            ]
        }


class SecurityGroupReadTest(unittest.TestCase):
    def test_real_shape_reports_non_compliant_without_mutation(self):
        ec2 = FakeEc2(
            [
                {
                    "IpProtocol": "tcp",
                    "FromPort": 22,
                    "ToPort": 22,
                    "IpRanges": [{"CidrIp": PUBLIC_IPV4}],
                }
            ]
        )
        result = check_security_group(ec2, "sg-demo")
        self.assertEqual(result["status"], "NON_COMPLIANT")
        self.assertEqual(result["source"], PUBLIC_IPV4)
        self.assertEqual(result["mutation"], "none")
        self.assertEqual(ec2.calls, 1)

    def test_compliant_state_is_clean_read_result(self):
        result = check_security_group(FakeEc2([]), "sg-demo")
        self.assertEqual(result["status"], "COMPLIANT")
        self.assertEqual(result["source"], "none")

    def test_handler_rejects_input_and_unknown_tool(self):
        context = SimpleNamespace(
            client_context=SimpleNamespace(
                custom={"bedrockAgentCoreToolName": "Target___check_security_group"}
            )
        )
        with self.assertRaisesRegex(ValueError, "fixed dev"):
            lambda_handler({"group_id": "sg-other"}, context)
        unknown = SimpleNamespace(
            client_context=SimpleNamespace(
                custom={"bedrockAgentCoreToolName": "Target___other"}
            )
        )
        with self.assertRaisesRegex(ValueError, "unknown"):
            lambda_handler({"environment": "dev"}, unknown)


if __name__ == "__main__":
    unittest.main()
