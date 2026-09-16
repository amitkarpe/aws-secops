import json
from pathlib import Path
import unittest

from pilot_v1.agentic_evidence import (
    S3_CONTROL,
    build_decision_timeline,
    build_s3_investigation,
)
from pilot_v1.multi_account_read import parse_scopes, read_two_accounts


ROOT = Path(__file__).resolve().parents[1]


def sample_plan(**overrides):
    value = {
        "version": 1,
        "control": S3_CONTROL,
        "config_noncompliant": 2,
        "owned_resources": 2,
        "candidate_owned": 2,
        "eligible_owned": 2,
        "provider_evidence_unknown": 0,
        "partial": False,
        "ready_to_prepare": True,
        "current_batch": {
            "batch_id": "a" * 64,
            "decision": "PENDING",
            "counts": {"PENDING": 2},
            "verified": 0,
            "total": 2,
            "execution_active": False,
        },
    }
    value.update(overrides)
    return value


def sample_status(**control_overrides):
    control = {
        "family": "s3",
        "compliant": 0,
        "noncompliant": 2,
        "unknown": 0,
        "evidence_source": "Saved S3 batch readback (not a fresh scan)",
        "config": {"counts": {"NON_COMPLIANT": 2}, "partial": False},
    }
    control.update(control_overrides)
    return {"version": 1, "controls": [control]}


def sample_page():
    return {
        "version": 1,
        "items": [{
            "resource": "aws-secops-bpa-secret-name-001",
            "before": {
                "BlockPublicAcls": False,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        }],
    }


class AgenticEvidenceTests(unittest.TestCase):
    def test_investigation_is_sanitized_and_read_only(self):
        result = build_s3_investigation(sample_plan(), sample_status(), sample_page())
        rendered = json.dumps(result)
        self.assertEqual(result["mutation"]["performed"], False)
        self.assertEqual(result["mutation"]["approval"], "REQUIRED_FOR_MUTATION")
        self.assertEqual(result["resource_identity"], "hidden-by-default")
        self.assertNotIn("aws-secops-bpa-secret-name-001", rendered)
        self.assertIn("not public data exposure", result["conclusion"])
        self.assertIn("No claim is made", result["uncertainty"])
        self.assertEqual(result["evidence"][-1]["value"]["BlockPublicAcls"], False)

    def test_partial_config_blocks_remediation_recommendation(self):
        plan = sample_plan(partial=True)
        result = build_s3_investigation(plan, sample_status(), sample_page())
        self.assertEqual(result["confidence"], "LOW")
        self.assertEqual(result["mutation"]["approval"], "NOT_READY")
        self.assertIn("incomplete", result["conclusion"].lower())
        self.assertIn("Refresh bounded Config evidence", result["recommendation"])

    def test_timeline_is_observable_evidence_not_chain_of_thought(self):
        plan = sample_plan()
        status = sample_status()
        investigation = build_s3_investigation(plan, status, sample_page())
        result = build_decision_timeline(investigation, plan, status)
        self.assertEqual(
            [item["stage"] for item in result["timeline"]],
            [
                "Finding", "Investigation", "Risk / Context", "Recommendation",
                "Policy", "Human Decision", "Exact Tool", "Provider Readback",
                "Compliance Result",
            ],
        )
        self.assertEqual(result["chain_of_thought"], "not-collected-and-not-displayed")
        stages = {item["stage"]: item for item in result["timeline"]}
        self.assertEqual(stages["Policy"]["status"], "NOT_CALLED")
        self.assertEqual(stages["Human Decision"]["status"], "PENDING")
        self.assertEqual(stages["Exact Tool"]["status"], "NOT_CALLED")

    def test_timeline_requires_provider_verification_for_pass(self):
        plan = sample_plan(current_batch={
            "decision": "APPROVED",
            "counts": {"COMPLETED": 2},
            "verified": 2,
            "total": 2,
            "execution_active": False,
        })
        status = sample_status(config={"counts": {}, "partial": False})
        investigation = build_s3_investigation(plan, status, sample_page())
        result = build_decision_timeline(investigation, plan, status)
        stages = {item["stage"]: item for item in result["timeline"]}
        self.assertEqual(stages["Provider Readback"]["status"], "PASS")
        self.assertEqual(stages["Compliance Result"]["status"], "NO_CURRENT_NONCOMPLIANT_RETURNED")


class MultiAccountReadTests(unittest.TestCase):
    def raw_scopes(self):
        return json.dumps([
            {"label": "lab-a", "profile": "read-a", "account_id": "111111111111", "region": "ap-southeast-1"},
            {"label": "lab-b", "profile": "read-b", "account_id": "222222222222", "region": "ap-southeast-1"},
        ])

    def test_exactly_two_distinct_accounts_required(self):
        scopes = parse_scopes(self.raw_scopes())
        self.assertEqual(len(scopes), 2)
        one = json.dumps([{"label": "lab-a", "profile": "read-a", "account_id": "111111111111", "region": "ap-southeast-1"}])
        with self.assertRaises(ValueError):
            parse_scopes(one)
        duplicate = json.dumps([
            {"label": "lab-a", "profile": "read-a", "account_id": "111111111111", "region": "ap-southeast-1"},
            {"label": "lab-b", "profile": "read-b", "account_id": "111111111111", "region": "ap-southeast-1"},
        ])
        with self.assertRaises(ValueError):
            parse_scopes(duplicate)

    def test_two_account_summary_hides_raw_ids_and_has_no_mutation(self):
        def fake_reader(scope, service, operation, arguments):
            if service == "sts":
                self.assertEqual(operation, "get-caller-identity")
                return {"Account": scope.account_id}
            self.assertEqual(service, "configservice")
            self.assertEqual(operation, "describe-compliance-by-config-rule")
            self.assertEqual(arguments[0], "--config-rule-names")
            return {
                "ComplianceByConfigRules": [
                    {"ConfigRuleName": S3_CONTROL, "Compliance": {"ComplianceType": "NON_COMPLIANT"}},
                    {"ConfigRuleName": "restricted-ssh", "Compliance": {"ComplianceType": "COMPLIANT"}},
                ]
            }

        result = read_two_accounts(self.raw_scopes(), fake_reader)
        rendered = json.dumps(result)
        self.assertEqual(result["mode"], "two-account-read-only")
        self.assertEqual(result["mutation"], False)
        self.assertEqual(len(result["accounts"]), 2)
        self.assertNotIn("111111111111", rendered)
        self.assertNotIn("222222222222", rendered)
        self.assertEqual({item["authority"] for item in result["accounts"]}, {"READ_ONLY"})


class IntegrationSafetyTests(unittest.TestCase):
    def test_new_agent_tools_are_read_only_and_executors_remain_separate(self):
        installer = (ROOT / "integration" / "install-compliance.cjs").read_text(encoding="utf-8")
        agent = json.loads((ROOT / "integration" / "compliance-agent.json").read_text(encoding="utf-8"))
        for tool in (
            "investigate_s3_context_mcp_aws_compliance_planner",
            "get_s3_decision_timeline_mcp_aws_compliance_planner",
        ):
            self.assertIn(tool, installer)
            self.assertIn(tool, agent["tools"])
        self.assertIn("start_batch_execution_mcp_aws_secops_executor", agent["tools"])
        self.assertIn("start_sg_batch_execution_mcp_aws_compliance", agent["tools"])
        self.assertIn("Never claim or expose hidden chain-of-thought", agent["instructions"])
        self.assertIn("READ-ONLY INTENT", agent["instructions"])


if __name__ == "__main__":
    unittest.main()
