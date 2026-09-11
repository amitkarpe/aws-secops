import unittest

from pilot_v1.sg_lambda import remediate


class FakeEC2:
    def __init__(self, *, attached=False, extra=False, compliant=False):
        self.attached = attached
        self.extra = extra
        self.compliant = compliant
        self.revoked = []

    def describe_security_groups(self, GroupIds):
        return {"SecurityGroups": [{
            "GroupId": GroupIds[0], "VpcId": "vpc-abc123", "GroupName": "aws-secops-ssh-" + "a" * 16 + "-000",
            "Tags": [{"Key": "project", "Value": "aws-secops"}, {"Key": "owner", "Value": "amit"},
                     {"Key": "phase", "Value": "bulk-ssh"}, {"Key": "run", "Value": "a" * 16}],
        }]}

    def describe_network_interfaces(self, **kwargs):
        return {"NetworkInterfaces": [{}] if self.attached else []}

    def describe_security_group_rules(self, **kwargs):
        rows = [] if self.compliant else [{
            "SecurityGroupRuleId": "sgr-abc123", "IsEgress": False, "IpProtocol": "tcp",
            "FromPort": 22, "ToPort": 22, "CidrIpv4": "0.0.0.0/0",
        }]
        if self.extra:
            rows.append({"SecurityGroupRuleId": "sgr-def456", "IsEgress": False, "IpProtocol": "tcp",
                         "FromPort": 80, "ToPort": 80, "CidrIpv4": "0.0.0.0/0"})
        return {"SecurityGroupRules": rows}

    def revoke_security_group_ingress(self, **kwargs):
        self.revoked.append(kwargs)
        self.compliant = True
        return {}


def manifest():
    return {"scope_hash": "b" * 64, "run": "a" * 16, "vpc_id": "vpc-abc123",
            "security_groups": [{"group_id": "sg-abc123", "name": "aws-secops-ssh-" + "a" * 16 + "-000"}]}


def event():
    return {"scope_hash": "b" * 64, "resource_index": 0, "batch_id": "c" * 64, "environment": "dev"}


class SGLambdaTests(unittest.TestCase):
    def test_exact_rule_only_is_revoked(self):
        ec2 = FakeEC2()
        result = remediate(ec2, manifest(), event())
        self.assertEqual(result["result"], "SSH_REVOKED")
        self.assertEqual(ec2.revoked, [{"GroupId": "sg-abc123", "SecurityGroupRuleIds": ["sgr-abc123"]}])

    def test_already_compliant_is_no_write(self):
        ec2 = FakeEC2(compliant=True)
        result = remediate(ec2, manifest(), event())
        self.assertEqual(result["result"], "ALREADY_COMPLIANT")
        self.assertFalse(ec2.revoked)

    def test_attached_extra_or_edited_scope_fails_before_write(self):
        for ec2 in (FakeEC2(attached=True), FakeEC2(extra=True)):
            with self.assertRaises(ValueError):
                remediate(ec2, manifest(), event())
            self.assertFalse(ec2.revoked)
        edited = event(); edited["environment"] = "prod"
        ec2 = FakeEC2()
        with self.assertRaises(ValueError):
            remediate(ec2, manifest(), edited)
        self.assertFalse(ec2.revoked)


if __name__ == "__main__":
    unittest.main()
