import json
from pathlib import Path
import unittest

from pilot_v1 import multi_account_read as mar
from pilot_v1.agentic_evidence import (
    BPA_TARGET,
    S3_CONTROL,
    build_decision_timeline,
    build_s3_investigation,
)
from pilot_v1.multi_account_read import parse_scopes, read_two_accounts


ROOT = Path(__file__).resolve().parents[1]
NONCOMPLIANT = {**BPA_TARGET, "BlockPublicAcls": False}


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


def batch_item(number, state="PENDING", before=None, after=None):
    return {
        "resource": f"aws-secops-bpa-secret-name-{number:03d}",
        "state": state,
        "before": dict(before or NONCOMPLIANT),
        "after": None if after is None else dict(after),
        "changed": None,
        "message": "test evidence",
    }


def sample_batch(items=None, *, decision="PENDING", complete=True, total=None):
    items = list(items or [batch_item(1), batch_item(2)])
    total = len(items) if total is None else total
    counts = {}
    for item in items:
        counts[item["state"]] = counts.get(item["state"], 0) + 1
    verified = sum(item["state"] in {"COMPLETED", "SKIPPED"} for item in items)
    return {
        "version": 1,
        "summary": {
            "batch_id": "a" * 64,
            "decision": decision,
            "counts": counts,
            "verified": verified,
            "total": total,
            "execution_active": any(item["state"] == "RUNNING" for item in items),
        },
        "total": total,
        "complete": complete,
        "items": items,
    }


class AgenticEvidenceTests(unittest.TestCase):
    def test_pending_preview_is_sanitized_and_precondition_only(self):
        result = build_s3_investigation(sample_plan(), sample_status(), sample_batch())
        rendered = json.dumps(result)
        self.assertEqual(result["result"], "ATTENTION")
        self.assertEqual(result["mutation"]["performed"], False)
        self.assertEqual(result["mutation"]["approval"], "REQUIRED_FOR_MUTATION")
        self.assertEqual(result["provider_evidence"]["mode"], "PREVIEW_NONCOMPLIANT")
        self.assertIn("preview/precondition", result["provider_evidence"]["message"])
        self.assertEqual(result["resource_identity"], "hidden-by-default")
        self.assertNotIn("aws-secops-bpa-secret-name", rendered)
        self.assertIn("not public data exposure", result["conclusion"])

    def test_partial_config_blocks_remediation_recommendation(self):
        plan = sample_plan(partial=True)
        status = sample_status(config={"counts": {"NON_COMPLIANT": 2}, "partial": True})
        result = build_s3_investigation(plan, status, sample_batch())
        self.assertEqual(result["confidence"], "LOW")
        self.assertEqual(result["mutation"]["approval"], "NOT_READY")
        timeline = build_decision_timeline(result, plan, status)
        stages = {item["stage"]: item for item in timeline["timeline"]}
        self.assertEqual(stages["Finding"]["status"], "PARTIAL")
        self.assertEqual(stages["Compliance Result"]["status"], "PARTIAL")

    def test_completed_batch_uses_after_and_does_not_recommend_again(self):
        batch = sample_batch([
            batch_item(1, "COMPLETED", before=NONCOMPLIANT, after=BPA_TARGET),
            batch_item(2, "SKIPPED", before=NONCOMPLIANT, after=BPA_TARGET),
        ], decision="APPROVE")
        plan = sample_plan(eligible_owned=0, provider_evidence_unknown=2, current_batch=batch["summary"])
        result = build_s3_investigation(plan, sample_status(), batch)
        self.assertEqual(result["provider_evidence"]["mode"], "VERIFIED_COMPLIANT")
        self.assertEqual(result["result"], "PROVIDER_COMPLIANT_CONFIG_LAG")
        self.assertEqual(result["mutation"]["approval"], "NOT_REQUIRED")
        self.assertIn("Do not remediate again", result["recommendation"])

    def test_config_lag_timeline_reports_provider_pass_separately(self):
        batch = sample_batch([
            batch_item(1, "COMPLETED", after=BPA_TARGET),
            batch_item(2, "COMPLETED", after=BPA_TARGET),
        ], decision="APPROVE")
        plan = sample_plan(eligible_owned=0, current_batch=batch["summary"])
        status = sample_status(config={"counts": {"NON_COMPLIANT": 2}, "partial": False})
        investigation = build_s3_investigation(plan, status, batch)
        timeline = build_decision_timeline(investigation, plan, status)
        stages = {item["stage"]: item for item in timeline["timeline"]}
        self.assertEqual(stages["Provider Readback"]["status"], "PASS")
        self.assertEqual(stages["Compliance Result"]["status"], "NON_COMPLIANT")
        self.assertEqual(stages["Recommendation"]["status"], "NO_ACTION")

    def test_mixed_terminal_provider_states_block_global_conclusion(self):
        batch = sample_batch([
            batch_item(1, "COMPLETED", after=BPA_TARGET),
            batch_item(2, "FAILED", after=None),
        ], decision="APPROVE")
        plan = sample_plan(eligible_owned=0, current_batch=batch["summary"])
        result = build_s3_investigation(plan, sample_status(), batch)
        self.assertEqual(result["provider_evidence"]["mode"], "INCOMPLETE_OR_UNCERTAIN")
        self.assertEqual(result["result"], "EVIDENCE_INCOMPLETE")
        self.assertEqual(result["mutation"]["approval"], "NOT_READY")

    def test_unknown_item_never_reports_provider_pass(self):
        batch = sample_batch([
            batch_item(1, "COMPLETED", after=BPA_TARGET),
            batch_item(2, "UNKNOWN", after=None),
        ], decision="APPROVE")
        plan = sample_plan(eligible_owned=0, current_batch=batch["summary"])
        investigation = build_s3_investigation(plan, sample_status(), batch)
        timeline = build_decision_timeline(investigation, plan, sample_status())
        stages = {item["stage"]: item for item in timeline["timeline"]}
        self.assertEqual(stages["Provider Readback"]["status"], "UNKNOWN")
        self.assertNotEqual(stages["Provider Readback"]["status"], "PASS")
        self.assertEqual(stages["Recommendation"]["status"], "BLOCKED")

    def test_partial_batch_never_classifies_from_first_item(self):
        batch = sample_batch(
            [batch_item(1, "COMPLETED", after=BPA_TARGET)],
            decision="APPROVE",
            complete=False,
            total=2,
        )
        plan = sample_plan(eligible_owned=0, current_batch=batch["summary"])
        result = build_s3_investigation(plan, sample_status(), batch)
        self.assertEqual(result["provider_evidence"]["mode"], "PARTIAL_BATCH")
        self.assertEqual(result["result"], "EVIDENCE_INCOMPLETE")

    def test_timeline_is_observable_evidence_not_chain_of_thought(self):
        plan = sample_plan()
        status = sample_status()
        investigation = build_s3_investigation(plan, status, sample_batch())
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
        self.assertEqual(stages["Provider Readback"]["status"], "PRECONDITION_ONLY")


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

    def test_operation_allowlist_is_exact(self):
        self.assertEqual(
            mar.ALLOWED_READS,
            {
                ("sts", "get-caller-identity"),
                ("configservice", "describe-compliance-by-config-rule"),
                ("ec2", "describe-vpcs"),
                ("iam", "get-account-summary"),
            },
        )
        scope = parse_scopes(self.raw_scopes())[0]
        with self.assertRaises(ValueError):
            mar._aws_json(scope, "iam", "list-roles", [])
        with self.assertRaises(ValueError):
            mar._aws_json(scope, "s3api", "get-bucket-policy", [])
        with self.assertRaises(ValueError):
            mar._aws_json(scope, "configservice", "describe-compliance-by-config-rule", [])

    def test_two_account_summary_hides_raw_identity_and_has_no_mutation(self):
        def fake_reader(scope, service, operation, arguments):
            if service == "sts":
                self.assertEqual(operation, "get-caller-identity")
                return {
                    "Account": scope.account_id,
                    "Arn": f"arn:aws:sts::{scope.account_id}:assumed-role/secops-read/session",
                }
            self.assertEqual(service, "configservice")
            self.assertEqual(operation, "describe-compliance-by-config-rule")
            self.assertEqual(arguments, ["--config-rule-names", S3_CONTROL, "restricted-ssh"])
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
        self.assertNotIn("arn:aws:sts", rendered)
        self.assertEqual({item["authority"] for item in result["accounts"]}, {"READ_ONLY_OPERATION_ALLOWLIST"})
        self.assertEqual({item["principal_kind"] for item in result["accounts"]}, {"ASSUMED_ROLE"})
        self.assertEqual({item["iam_scope"] for item in result["accounts"]}, {"RUNTIME_VERIFICATION_REQUIRED"})

    def test_three_to_four_account_overview_and_drill_down_hide_identifiers(self):
        raw = json.dumps([
            {"label": "lab-dev", "profile": "read-a", "account_id": "111111111111", "region": "ap-southeast-1"},
            {"label": "lab-poc", "profile": "read-b", "account_id": "222222222222", "region": "ap-southeast-1"},
            {"label": "lab-qa", "profile": "read-c", "account_id": "333333333333", "region": "ap-southeast-1"},
            {"label": "lab-sec", "profile": "read-d", "account_id": "444444444444", "region": "ap-southeast-1"},
        ])

        def fake_reader(scope, service, operation, arguments):
            if service == "sts":
                return {"Account": scope.account_id, "Arn": f"arn:aws:sts::{scope.account_id}:assumed-role/secops-read/session"}
            if service == "configservice":
                return {"ComplianceByConfigRules": [{"ConfigRuleName": S3_CONTROL, "Compliance": {"ComplianceType": "NON_COMPLIANT"}}]}
            if service == "ec2":
                self.assertEqual((operation, arguments), ("describe-vpcs", []))
                return {"Vpcs": [{}, {}]}
            if service == "iam":
                self.assertEqual((operation, arguments), ("get-account-summary", []))
                return {"SummaryMap": {"Users": 1, "Roles": 2, "Policies": 3}}
            self.fail("unexpected read")

        overview = mar.read_security_overview(raw, fake_reader)
        drill_down = mar.drill_down_control(overview, "lab-sec", S3_CONTROL)
        rendered = json.dumps({"overview": overview, "drill_down": drill_down})
        self.assertEqual(overview["mode"], "3-4-account-read-only-overview")
        self.assertEqual(len(overview["accounts"]), 4)
        self.assertFalse(overview["mutation"])
        self.assertEqual(drill_down["config_state"], "NON_COMPLIANT")
        self.assertFalse(drill_down["mutation"])
        self.assertNotIn("111111111111", rendered)
        self.assertNotIn("arn:aws:sts", rendered)

    def test_overview_rejects_out_of_range_or_duplicate_scopes(self):
        with self.assertRaises(ValueError):
            mar.parse_overview_scopes(self.raw_scopes())
        duplicate = json.dumps([
            {"label": "lab-a", "profile": "read-a", "account_id": "111111111111", "region": "ap-southeast-1"},
            {"label": "lab-b", "profile": "read-a", "account_id": "222222222222", "region": "ap-southeast-1"},
            {"label": "lab-c", "profile": "read-c", "account_id": "333333333333", "region": "ap-southeast-1"},
        ])
        with self.assertRaises(ValueError):
            mar.parse_overview_scopes(duplicate)

    def test_overview_marks_config_unavailable_without_mutation(self):
        raw = json.dumps([
            {"label": "lab-a", "profile": "read-a", "account_id": "111111111111", "region": "ap-southeast-1"},
            {"label": "lab-b", "profile": "read-b", "account_id": "222222222222", "region": "ap-southeast-1"},
            {"label": "lab-c", "profile": "read-c", "account_id": "333333333333", "region": "ap-southeast-1"},
        ])

        def fake_reader(scope, service, operation, arguments):
            if service == "sts":
                return {"Account": scope.account_id, "Arn": f"arn:aws:sts::{scope.account_id}:assumed-role/secops-read/session"}
            if service == "configservice":
                raise RuntimeError("Config is unavailable")
            if service == "ec2":
                return {"Vpcs": []}
            if service == "iam":
                return {"SummaryMap": {"Users": 0, "Roles": 0, "Policies": 0}}
            self.fail("unexpected read")

        overview = mar.read_security_overview(raw, fake_reader)
        drill_down = mar.drill_down_control(overview, "lab-a", S3_CONTROL)
        self.assertEqual(overview["accounts"][0]["security"]["evidence"], "CONFIG_UNAVAILABLE")
        self.assertEqual(drill_down["config_state"], "UNAVAILABLE")
        self.assertFalse(drill_down["mutation"])


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
