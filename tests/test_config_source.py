import unittest
from unittest.mock import patch

from pilot_v1.config_source import fetch_config_findings, normalize_evaluation
from pilot_v1.service import PilotService
from tests import test_service


def evaluation():
    return {
        "EvaluationResultIdentifier": {"EvaluationResultQualifier": {
            "ResourceId": "synthetic-resource", "ResourceType": "AWS::EC2::SecurityGroup",
            "ConfigRuleName": "synthetic-ssh-control"}},
        "ComplianceType": "NON_COMPLIANT", "ResultRecordedTime": "2026-09-09T01:00:00+00:00",
        "Annotation": "Synthetic evaluation evidence.",
    }


class ConfigSourceTest(unittest.TestCase):
    @patch("pilot_v1.config_source._read")
    def test_bounded_fetch_maps_provider_time_and_marks_partial(self, read):
        read.side_effect = [
            {"ConfigurationRecordersStatus": [{"recording": True, "lastStatus": "SUCCESS"}]},
            {"ComplianceByConfigRules": [{"ConfigRuleName": "synthetic-ssh-control"}]},
            {"EvaluationResults": [evaluation()], "NextToken": "synthetic-token"},
        ]
        result = fetch_config_findings()
        self.assertEqual(result["status"], "PARTIAL")
        finding = result["findings"][0]
        self.assertEqual(finding["observed_at"], "2026-09-09T01:00:00+00:00")
        self.assertEqual((finding["source"], finding["severity"]), ("AWS Config", "INFO"))
        self.assertEqual(read.call_count, 3)
        self.assertIn("100", read.call_args.args[1])

    def test_sync_routes_provider_evidence_and_retains_snapshot_on_error(self):
        batch = {"findings": [normalize_evaluation(evaluation())],
                 "synced_at": "2026-09-10T01:00:00+00:00", "status": "SUCCESS", "scope": "bounded"}
        calls = []
        def harness(config, prompt, **options):
            calls.append(options)
            return {"response": "AWS Config recorded synthetic evidence; PLAN_ONLY.",
                    "tool_calls": 0, "tool_results": []}
        service = PilotService(test_service.ServiceTest().config(), harness_call=harness,
                               provider_fetch=lambda: batch)
        state = service.sync_provider()
        self.assertEqual(state["finding"]["evidence_origin"], "AWS_PROVIDER")
        self.assertEqual(state["audit"]["action_eligibility"], "PLAN_ONLY")
        self.assertTrue(calls[0]["explanation_only"])
        self.assertIn("AWS Config evaluations", calls[0]["system_prompt"])
        self.assertIn("AWS_PROVIDER", service.export_csv())
        self.assertIn(batch["synced_at"], service.export_markdown())
        with self.assertRaises(RuntimeError):
            service.approve("dev")
        service.sync_provider()
        self.assertEqual(service.backlog()["total_open"], 1)
        def unavailable():
            raise RuntimeError("private error must not be exposed")
        service.provider_fetch = unavailable
        with self.assertRaisesRegex(RuntimeError, "previous snapshot retained"):
            service.sync_provider()
        self.assertEqual(service.source_status["status"], "ERROR")
        self.assertEqual(service.backlog()["total_open"], 1)
        self.assertEqual(service.source_status["last_success"], batch["synced_at"])
        service.provider_fetch = lambda: dict(batch, findings=[])
        service.sync_provider()
        self.assertEqual(service.backlog()["total_open"], 1)
        self.assertFalse(service.backlog()["open_findings"][0]["seen_in_latest_sync"])

    @patch("pilot_v1.config_source._read")
    def test_inactive_recorder_and_invalid_time_are_not_fresh_success(self, read):
        read.return_value = {"ConfigurationRecordersStatus": []}
        with self.assertRaisesRegex(RuntimeError, "recorder"):
            fetch_config_findings()
        value = evaluation()
        value["ResultRecordedTime"] = "2026-09-09T01:00:00"
        with self.assertRaisesRegex(ValueError, "timezone"):
            normalize_evaluation(value)
