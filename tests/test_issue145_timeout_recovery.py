from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from pilot_v1.codebuild_execution import BuildError
from pilot_v1.multi_account_campaign import SG_CONTROL
from pilot_v1.operator_server import OperatorService


class Issue145TimeoutRecoveryTests(unittest.TestCase):
    def make_service(self, *, state: str = "EXECUTING", age_seconds: int = 0) -> tuple[OperatorService, Path]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "four-account-execution-plan.json"
        plan = {
            "version": 1,
            "plans": {
                SG_CONTROL: {
                    "control": SG_CONTROL,
                    "batch_id": "a" * 20,
                    "pending_aliases": ["lab-poc", "lab-qa", "lab-sec"],
                    "excluded_aliases": ["lab-dev"],
                    "exclude_resources": ["aws-secops-issue82-lab-dev"],
                    "exception": {
                        "reason": "approved risk acceptance",
                        "reference": "RA-DEMO-141",
                        "expires_at": None,
                        "requested_at": "2026-09-20T13:56:08Z",
                    },
                    "scope_hash": "b" * 24,
                    "created_at": int(time.time()) - age_seconds,
                    "execution_state": state,
                }
            },
        }
        path.write_text(json.dumps(plan))
        service = object.__new__(OperatorService)
        service.execution_state = path
        service.multi_account_status = lambda: {
            "accounts": [
                {"alias": alias, "controls": {SG_CONTROL: "NON_COMPLIANT"}}
                for alias in ("lab-dev", "lab-poc", "lab-qa", "lab-sec")
            ]
        }
        return service, path

    @staticmethod
    def recovered_plan(*_args, **_kwargs):
        return {
            "control": SG_CONTROL,
            "batch_id": "a" * 20,
            "decision": "ALREADY_COMPLIANT",
            "mutation_count": 0,
            "provider_verified": False,
            "pending_aliases": [],
            "excluded_aliases": ["lab-dev"],
            "excluded_count": 1,
            "config": {
                "lab-dev": "NON_COMPLIANT",
                "lab-poc": "COMPLIANT",
                "lab-qa": "COMPLIANT",
                "lab-sec": "COMPLIANT",
            },
            "account_ids": "hidden-by-default",
            "resource_identifiers": "hidden-by-default",
        }

    def test_retry_recovers_verified_success_without_second_execute_dispatch(self):
        service, path = self.make_service()
        calls = []

        def fake_run(mode, *args, **kwargs):
            calls.append(mode)
            return self.recovered_plan()

        with patch("pilot_v1.operator_server.run_four_account_build", side_effect=fake_run):
            result = service.execute_multi_account(SG_CONTROL, "a" * 20, "b" * 24)

        self.assertEqual(calls, ["plan"])
        self.assertEqual(result["decision"], "RECOVERED_VERIFIED")
        self.assertIsNone(result["mutation_count"])
        self.assertEqual(result["verified_included_count"], 3)
        self.assertTrue(result["provider_verified"])
        self.assertTrue(result["excluded_resources_unchanged"])
        self.assertTrue(result["recovered_after_timeout"])
        self.assertNotIn(SG_CONTROL, json.loads(path.read_text())["plans"])

    def test_expired_batch_can_only_reconcile_verified_completion(self):
        service, path = self.make_service(state="PENDING_APPROVAL", age_seconds=1800)

        with patch(
            "pilot_v1.operator_server.run_four_account_build",
            side_effect=self.recovered_plan,
        ) as run:
            result = service.execute_multi_account(SG_CONTROL, "a" * 20, "b" * 24)

        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.args[0], "plan")
        self.assertEqual(result["decision"], "RECOVERED_VERIFIED")
        self.assertNotIn(SG_CONTROL, json.loads(path.read_text())["plans"])

    def test_expired_unresolved_batch_never_dispatches(self):
        service, path = self.make_service(state="PENDING_APPROVAL", age_seconds=1800)

        def fake_run(mode, *args, **kwargs):
            self.assertEqual(mode, "plan")
            return {
                **self.recovered_plan(),
                "decision": "PLAN",
                "pending_aliases": ["lab-poc", "lab-qa", "lab-sec"],
            }

        with patch("pilot_v1.operator_server.run_four_account_build", side_effect=fake_run):
            with self.assertRaisesRegex(RuntimeError, "expired frozen batch"):
                service.execute_multi_account(SG_CONTROL, "a" * 20, "b" * 24)

        self.assertIn(SG_CONTROL, json.loads(path.read_text())["plans"])

    def test_retry_does_not_redispatch_while_provider_state_is_unchanged(self):
        service, path = self.make_service()
        calls = []

        def fake_run(mode, *args, **kwargs):
            calls.append(mode)
            return {
                **self.recovered_plan(),
                "decision": "PLAN",
                "pending_aliases": ["lab-poc", "lab-qa", "lab-sec"],
            }

        with patch("pilot_v1.operator_server.run_four_account_build", side_effect=fake_run):
            with self.assertRaisesRegex(RuntimeError, "no second execution was dispatched"):
                service.execute_multi_account(SG_CONTROL, "a" * 20, "b" * 24)

        self.assertEqual(calls, ["plan"])
        saved = json.loads(path.read_text())["plans"][SG_CONTROL]
        self.assertEqual(saved["execution_state"], "EXECUTING")

    def test_partial_provider_state_fails_closed(self):
        service, _ = self.make_service()

        def fake_run(mode, *args, **kwargs):
            return {
                **self.recovered_plan(),
                "decision": "PLAN",
                "pending_aliases": ["lab-qa"],
            }

        with patch("pilot_v1.operator_server.run_four_account_build", side_effect=fake_run):
            with self.assertRaisesRegex(RuntimeError, "partial provider state"):
                service.execute_multi_account(SG_CONTROL, "a" * 20, "b" * 24)

    def test_changed_excluded_scope_fails_closed(self):
        service, _ = self.make_service()

        def fake_run(mode, *args, **kwargs):
            return {
                **self.recovered_plan(),
                "excluded_aliases": [],
                "excluded_count": 0,
            }

        with patch("pilot_v1.operator_server.run_four_account_build", side_effect=fake_run):
            with self.assertRaisesRegex(RuntimeError, "excluded resource changed"):
                service.execute_multi_account(SG_CONTROL, "a" * 20, "b" * 24)

    def test_normal_execute_marks_durable_state_before_dispatch(self):
        service, path = self.make_service(state="PENDING_APPROVAL")
        observed_state = []

        def fake_run(mode, *args, **kwargs):
            self.assertEqual(mode, "execute")
            observed_state.append(
                json.loads(path.read_text())["plans"][SG_CONTROL]["execution_state"]
            )
            return {
                "control": SG_CONTROL,
                "batch_id": "a" * 20,
                "decision": "APPROVE",
                "mutation_count": 3,
                "provider_verified": True,
                "included_aliases": ["lab-poc", "lab-qa", "lab-sec"],
                "excluded_aliases": ["lab-dev"],
                "excluded_count": 1,
                "config": {},
                "execution_backend": "AWS CodeBuild via GitHub CodeConnections",
                "account_ids": "hidden-by-default",
                "resource_identifiers": "hidden-by-default",
            }

        with patch("pilot_v1.operator_server.run_four_account_build", side_effect=fake_run):
            result = service.execute_multi_account(SG_CONTROL, "a" * 20, "b" * 24)

        self.assertEqual(observed_state, ["EXECUTING"])
        self.assertEqual(result["decision"], "APPROVE")
        self.assertEqual(result["mutation_count"], 3)
        self.assertFalse(result["recovered_after_timeout"])
        self.assertNotIn(SG_CONTROL, json.loads(path.read_text())["plans"])

    def test_timeout_keeps_executing_state_for_reconciliation(self):
        service, path = self.make_service(state="PENDING_APPROVAL")

        with patch(
            "pilot_v1.operator_server.run_four_account_build",
            side_effect=BuildError("bounded CodeBuild execution timed out"),
        ):
            with self.assertRaises(BuildError):
                service.execute_multi_account(SG_CONTROL, "a" * 20, "b" * 24)

        saved = json.loads(path.read_text())["plans"][SG_CONTROL]
        self.assertEqual(saved["execution_state"], "EXECUTING")


if __name__ == "__main__":
    unittest.main()
