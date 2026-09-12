import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pilot_v1.control_catalog import CONTROL_CATALOG, get_control
from pilot_v1.demo_prepare import (
    S3_NONCOMPLIANT, SG_NONCOMPLIANT, count_s3, count_sg, require_resettable, reset_s3, reset_sg,
)
from pilot_v1.log_proof import count_lambda_starts
from pilot_v1.operator_protocol import ConfirmationGate
from pilot_v1.operator_server import OperatorService


class ConfirmationGateTests(unittest.TestCase):
    def test_one_use_and_scope_bound(self):
        gate = ConfirmationGate(30)
        fingerprint = "a" * 64
        token = gate.issue("s3", fingerprint)
        gate.consume(token, "s3", fingerprint)
        with self.assertRaises(ValueError):
            gate.consume(token, "s3", fingerprint)

    def test_wrong_family_consumes_and_rejects(self):
        gate = ConfirmationGate(30)
        token = gate.issue("sg", "b" * 64)
        with self.assertRaises(ValueError):
            gate.consume(token, "s3", "b" * 64)
        with self.assertRaises(ValueError):
            gate.consume(token, "sg", "b" * 64)

    def test_new_token_invalidates_older_same_family(self):
        gate = ConfirmationGate(30)
        old = gate.issue("s3", "c" * 64)
        new = gate.issue("s3", "c" * 64)
        with self.assertRaises(ValueError):
            gate.consume(old, "s3", "c" * 64)
        gate.consume(new, "s3", "c" * 64)


class CatalogTests(unittest.TestCase):
    def test_only_two_exact_controls(self):
        self.assertEqual(set(CONTROL_CATALOG), {
            "s3-bucket-level-public-access-prohibited", "restricted-ssh"
        })
        self.assertEqual(get_control("restricted-ssh")["executor"], "start_sg_batch_execution")
        with self.assertRaises(ValueError):
            get_control("made-up")


class ResetGateTests(unittest.TestCase):
    def test_blocks_pending_active_and_unknown(self):
        for summary in [
            {"batch_id": "x", "execution_active": True, "counts": {}},
            {"batch_id": "x", "execution_active": False, "counts": {"PENDING": 1}},
            {"batch_id": "x", "execution_active": False, "counts": {"UNKNOWN": 1}},
        ]:
            with self.assertRaises(ValueError):
                require_resettable(summary)
        require_resettable({"batch_id": "x", "execution_active": False, "counts": {"COMPLETED": 10}})


class FakeS3:
    def __init__(self):
        from pilot_v1.bulk import TARGET
        self.resources = ["one", "two"]
        self.values = {"one": dict(TARGET), "two": dict(S3_NONCOMPLIANT)}
        self.calls = []

    def read(self, resource):
        return dict(self.values[resource])

    def guard(self, resource):
        return {"bucket": resource, "expected_bucket_owner": "123"}

    def call(self, service, operation, **kwargs):
        self.calls.append((service, operation, kwargs))
        if operation != "put-public-access-block":
            raise AssertionError("unexpected operation")
        self.values[kwargs["bucket"]] = dict(kwargs["public_access_block_configuration"])
        return {}


class FakeEC2:
    def __init__(self, parent):
        self.parent = parent
        self.calls = []

    def authorize_security_group_ingress(self, **kwargs):
        self.calls.append(kwargs)
        self.parent.values[kwargs["GroupId"]] = dict(SG_NONCOMPLIANT)


class FakeSG:
    def __init__(self):
        self.resources = ["sg-1", "sg-2"]
        self.values = {"sg-1": {"unrestricted_ssh": False}, "sg-2": dict(SG_NONCOMPLIANT)}
        self.ec2 = FakeEC2(self)
        self._demo_reset_client = self.ec2
        self.guarded = []

    def read(self, resource):
        return dict(self.values[resource])

    def guard(self, resource):
        self.guarded.append(resource)


class DemoResetTests(unittest.TestCase):
    def test_s3_reset_exact_and_idempotent(self):
        p = FakeS3()
        result = reset_s3(p)
        self.assertEqual(result, {"total": 2, "changed": 1, "already_noncompliant": 1})
        self.assertEqual(p.values["one"], S3_NONCOMPLIANT)
        self.assertEqual(len(p.calls), 1)
        self.assertEqual(p.calls[0][0:2], ("s3api", "put-public-access-block"))
        self.assertEqual(reset_s3(p)["changed"], 0)

    def test_sg_reset_only_exact_ssh(self):
        p = FakeSG()
        result = reset_sg(p)
        self.assertEqual(result, {"total": 2, "changed": 1, "already_noncompliant": 1})
        self.assertEqual(len(p.ec2.calls), 1)
        permission = p.ec2.calls[0]["IpPermissions"]
        self.assertEqual(permission, [{
            "IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
            "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "aws-secops restricted-ssh demo"}],
        }])

    def test_provider_counts_never_treat_read_error_as_compliant(self):
        s3 = FakeS3()
        original = s3.read
        s3.read = lambda resource: (_ for _ in ()).throw(RuntimeError("boom")) if resource == "two" else original(resource)
        self.assertEqual(count_s3(s3), {"total": 2, "compliant": 1, "noncompliant": 0, "unknown": 1})
        sg = FakeSG()
        original_sg = sg.read
        sg.read = lambda resource: (_ for _ in ()).throw(RuntimeError("boom")) if resource == "sg-2" else original_sg(resource)
        self.assertEqual(count_sg(sg), {"total": 2, "compliant": 1, "noncompliant": 0, "unknown": 1})


class FakeLogs:
    def __init__(self, pages):
        self.pages = list(pages)
        self.calls = []

    def filter_log_events(self, **kwargs):
        self.calls.append(kwargs)
        return self.pages.pop(0)


class LogProofTests(unittest.TestCase):
    def test_follows_legitimate_pagination(self):
        logs = FakeLogs([
            {"events": [{"id": "1"}], "nextToken": "a"},
            {"events": [{"id": "2"}], "nextToken": "b"},
            {"events": [{"id": "3"}]},
        ])
        self.assertEqual(count_lambda_starts(logs, "/aws/lambda/demo", 1, 2), 3)
        self.assertEqual(logs.calls[1]["nextToken"], "a")

    def test_repeated_token_is_rejected(self):
        logs = FakeLogs([
            {"events": [], "nextToken": "a"},
            {"events": [], "nextToken": "a"},
        ])
        with self.assertRaises(RuntimeError):
            count_lambda_starts(logs, "/aws/lambda/demo", 1, 2)

    def test_event_ceiling_is_rejected(self):
        logs = FakeLogs([{"events": [{"id": str(i)} for i in range(2)], "nextToken": "x"}])
        with self.assertRaises(RuntimeError):
            count_lambda_starts(logs, "/aws/lambda/demo", 1, 2, max_events=2)


class StatusResilienceTests(unittest.TestCase):
    def test_s3_batch_truth_survives_config_failure(self):
        class Provider:
            resources = ["one", "two"]

        class Bulk:
            provider = Provider()
            data = {"created_at": "2026-09-12T00:00:00+00:00"}
            path = ROOT / "does-not-exist.json"

            @staticmethod
            def summary():
                return {"batch_id": "a" * 64, "decision": "PENDING", "verified": 0,
                        "counts": {"PENDING": 2}, "total": 2}

        service = object.__new__(OperatorService)
        service.bulk = Bulk()
        service._config_control = lambda _control: (_ for _ in ()).throw(RuntimeError("config down"))
        result = service.s3_status()
        self.assertTrue(result["status_available"])
        self.assertFalse(result["config_available"])
        self.assertEqual(result["resource_count"], 2)
        self.assertEqual(result["noncompliant"], 2)
        self.assertEqual(result["batch"]["decision"], "PENDING")

    def test_aggregate_status_degrades_one_family_without_failing_all(self):
        service = object.__new__(OperatorService)
        service.s3_status = lambda: {
            "version": 1, "family": "s3", "title": "S3 Block Public Access",
            "resource_count": 100, "compliant": 0, "noncompliant": 100, "unknown": 0,
            "last_verification_time": None, "batch": {"batch_id": "x", "decision": "PENDING"},
            "config": None, "status_available": True, "config_available": False,
            "status_error": None, "config_error": "AWS Config status unavailable",
            "action": "enable BPA",
        }
        service._sg = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("sg down"))
        result = OperatorService.status(service)
        self.assertTrue(result["degraded"])
        self.assertEqual(len(result["controls"]), 2)
        self.assertTrue(result["controls"][0]["status_available"])
        self.assertFalse(result["controls"][1]["status_available"])
        self.assertIn("Provider/batch truth is shown where available", result["message"])


class OperatorPageTests(unittest.TestCase):
    def test_simple_two_card_ui_and_no_reset_all(self):
        html = (ROOT / "pilot_v1/static/operator.html").read_text()
        self.assertIn("S3 Block Public Access", html)
        self.assertIn("Security Group restricted SSH", html)
        self.assertIn("Prepare S3 demo", html)
        self.assertIn("Prepare SG demo", html)
        self.assertIn("https://sec.astromedicomp.org/", html)
        self.assertIn("Advanced / Legacy", html)
        self.assertIn("status-note", html)
        self.assertIn("temporarily unavailable", html)
        self.assertNotIn("Prepare all", html)
        self.assertNotIn("reset --all", html)

    def test_agent_has_unified_planner_but_no_reset_tool(self):
        agent = json.loads((ROOT / "integration/compliance-agent.json").read_text())
        self.assertEqual(agent["name"], "AWS Compliance Agent")
        tools = set(agent["tools"])
        self.assertIn("get_remediation_plan_mcp_aws_compliance_planner", tools)
        self.assertIn("prepare_remediation_mcp_aws_compliance_planner", tools)
        self.assertNotIn("prepare_remediation_batch_mcp_aws_compliance_planner", tools)
        self.assertNotIn("prepare_eligible_remediation_batches_mcp_aws_compliance_planner", tools)
        self.assertFalse(any("reset" in tool.lower() or "prepare_demo" in tool.lower() for tool in tools))
        planner = (ROOT / "pilot_v1/operator_mcp.py").read_text()
        self.assertNotIn("reset_s3", planner)
        self.assertNotIn("reset_sg", planner)


if __name__ == "__main__":
    unittest.main()
