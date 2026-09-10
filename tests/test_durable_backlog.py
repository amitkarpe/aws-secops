import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pilot_v1.backlog import FindingBacklog
from pilot_v1.service import PilotService
from tests.test_backlog import finding
from tests import test_service


PLAN = dict(owner="Lab operator", mitigation_plan="Review exact control before separate change.",
            target="next review", planning_status="PLANNED")


class DurableBacklogTest(unittest.TestCase):
    def test_restart_reconcile_preserves_plan_and_identity_without_closing_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "backlog.json"
            backlog = FindingBacklog(path=path)
            item = finding(source="AWS Config")
            backlog.replace_provider("AWS Config", [item, item], item["observed_at"])
            first = backlog.open_findings()[0]
            self.assertEqual(first["occurrence_count"], 1)
            backlog.update_plan(first["finding_id"], PLAN)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            restored = FindingBacklog(path=path)
            restored.replace_provider("AWS Config", [item], item["observed_at"])
            second = restored.open_findings()[0]
            self.assertEqual(second["finding_id"], first["finding_id"])
            self.assertEqual(second["first_seen"], first["first_seen"])
            self.assertEqual(second["occurrence_count"], 2)
            self.assertEqual({key: second[key] for key in PLAN}, PLAN)
            restored.replace_provider("AWS Config", [], item["observed_at"])
            missing = FindingBacklog(path=path).open_findings()[0]
            self.assertFalse(missing["seen_in_latest_sync"])
            self.assertEqual(missing["status"], "NON_COMPLIANT")
            self.assertEqual(missing["action_eligibility"], "PLAN_ONLY")

    def test_bad_store_and_failed_replace_do_not_destroy_previous_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "backlog.json"
            backlog = FindingBacklog([finding()], path=path)
            before = path.read_bytes()
            with patch("pilot_v1.backlog.os.replace", side_effect=OSError("disk unavailable")):
                with self.assertRaisesRegex(RuntimeError, "previous state retained"):
                    backlog.upsert([finding(status="COMPLIANT")])
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(backlog.summary()["total_open"], 1)
            for invalid in (b"{", json.dumps({"version": 999, "findings": []}).encode()):
                path.write_bytes(invalid)
                with self.assertRaisesRegex(RuntimeError, "startup stopped"):
                    FindingBacklog(path=path)
                self.assertEqual(path.read_bytes(), invalid)

    def test_import_is_atomic_and_cannot_change_existing_operator_plan(self):
        backlog = FindingBacklog([finding()])
        item = backlog.open_findings()[0]
        backlog.update_plan(item["finding_id"], PLAN)
        backlog.upsert([finding(owner="untrusted imported owner", target="untrusted date")])
        self.assertEqual(backlog.open_findings()[0]["owner"], PLAN["owner"])
        before = backlog.summary()
        with self.assertRaises(ValueError):
            backlog.upsert([finding(resource_id="second"), finding(finding_id="forged")])
        self.assertEqual(backlog.summary(), before)
        with self.assertRaises(ValueError):
            backlog.upsert([finding(resource_id=f"resource-{i}") for i in range(101)])
        self.assertEqual(backlog.summary(), before)

    def test_failed_sync_preserves_durable_plan_and_planning_never_calls_aws(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "backlog.json")
            def forbidden(*args, **kwargs):
                raise RuntimeError("not available")
            service = PilotService(test_service.ServiceTest().config(), backlog_path=path,
                                   provider_fetch=forbidden, harness_call=forbidden, gateway_call=forbidden)
            service.findings.upsert([finding(source="AWS Config")], evidence_origin="AWS_PROVIDER")
            identity = service.backlog()["open_findings"][0]["finding_id"]
            payload = dict(finding_id=identity, **PLAN)
            service.update_plan(payload)
            before = Path(path).read_bytes()
            with self.assertRaises(RuntimeError):
                service.sync_provider()
            self.assertEqual(Path(path).read_bytes(), before)
            self.assertIn(PLAN["mitigation_plan"], service.export_csv())
            self.assertIn(identity, service.export_markdown())
            for bad in (dict(payload, status="COMPLIANT"), dict(payload, finding_id="0" * 64),
                        dict(payload, owner="x" * 129), dict(payload, planning_status="VERIFIED")):
                with self.assertRaises(ValueError):
                    service.update_plan(bad)
            self.assertEqual(Path(path).read_bytes(), before)
            with self.assertRaises(RuntimeError):
                service.approve("dev")
