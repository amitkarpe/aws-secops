import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from pilot_v1.service import PilotService
from pilot_v1.jobs import JobStore
from tests import test_service
from tests.test_backlog import finding


class JobTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = str(Path(self.directory.name) / "backlog.json")
        self.fake = test_service.ServiceTest()
        self.fake.setUp()
        self.calls = []
        def gateway(*args):
            self.calls.append(args[-2])
            return self.fake.gateway(*args)
        self.service = PilotService(self.fake.config(), harness_call=self.fake.harness,
                                    gateway_call=gateway, backlog_path=self.path)

    def test_job_is_single_use_reject_no_call_then_approve_and_restart(self):
        pending = self.service.check()["job"]
        self.assertEqual(self.service.check()["job"]["job_id"], pending["job_id"])
        self.assertEqual(pending["environment"], "dev")
        self.assertEqual(pending["action"], "remove_unrestricted_ssh")
        self.service.decide_job(pending["job_id"], "REJECT")
        self.assertEqual(self.calls, [])
        with self.assertRaises(ValueError):
            self.service.decide_job(pending["job_id"], "APPROVE")
        pending = self.service.check()["job"]
        done = self.service.decide_job(pending["job_id"], "APPROVE")["job"]
        self.assertEqual((done["state"], done["provider_after"], done["changed"]), ("COMPLETED", "COMPLIANT", True))
        self.assertEqual(self.calls.count("remediate_tool"), 1)
        before = list(self.calls)
        restarted = PilotService(self.fake.config(), backlog_path=self.path, gateway_call=lambda *a: self.fail("restart called AWS"))
        self.assertEqual(restarted.jobs.get(done["job_id"]), done)
        with self.assertRaises(ValueError):
            restarted.decide_job(done["job_id"], "APPROVE")
        self.assertEqual(self.calls, before)

    def test_plan_only_cannot_create_job(self):
        for source, origin in (("AWS Config", "AWS_PROVIDER"), ("CloudSCAPE", "IMPORTED"), ("VAPT", "IMPORTED"), ("AWS EC2", "IMPORTED")):
            self.service.findings.upsert([finding(source=source)], evidence_origin=origin)
        for item in self.service.findings.open_findings():
            with self.assertRaises(ValueError):
                self.service.create_job(item["finding_id"])
        self.assertEqual(self.calls, [])

    def test_failed_save_and_interrupted_dispatch_never_replay(self):
        pending = self.service.check()["job"]
        with patch.object(self.service.jobs, "_save", side_effect=RuntimeError("disk failed")):
            with self.assertRaises(RuntimeError):
                self.service.decide_job(pending["job_id"], "APPROVE")
        self.assertEqual(self.calls, [])
        self.service.jobs.update(pending["job_id"], state="EXECUTING", human_decision="APPROVE")
        restarted = JobStore(Path(self.path).with_suffix(".jobs.json"))
        failed = restarted.get(pending["job_id"])
        self.assertEqual(failed["state"], "FAILED")
        self.assertIsNone(failed["changed"])
        self.assertIn("no automatic retry", failed["message"])

    def test_wrong_verification_and_generic_tool_errors_are_failed_not_success_or_deny(self):
        pending = self.service.check()["job"]
        def erroneous(*args):
            if args[-2] == "read_tool":
                return self.fake.gateway(*args)
            return {"result": {"isError": True, "content": []}}
        self.service.gateway_call = erroneous
        result = self.service.decide_job(pending["job_id"], "APPROVE")["job"]
        self.assertEqual(result["state"], "FAILED")
        self.assertIsNone(result["changed"])
        pending = self.service.check()["job"]
        def unverified(*args):
            result = self.fake.gateway(*args)
            self.fake.provider_status = "NON_COMPLIANT"
            return result
        self.service.gateway_call = unverified
        result = self.service.decide_job(pending["job_id"], "APPROVE")["job"]
        self.assertEqual(result["state"], "FAILED")
        self.assertTrue(result["changed"])

    def test_corrupt_and_full_journal_fail_without_destroying_history(self):
        job = self.service.check()["job"]
        with patch("pilot_v1.jobs.MAX_JOBS", 1):
            self.service.decide_job(job["job_id"], "REJECT")
            with self.assertRaises(ValueError):
                self.service.check()
        self.assertEqual(len(self.service.jobs.history()), 1)
        path = Path(self.path).with_suffix(".jobs.json")
        path.write_text("{")
        with self.assertRaisesRegex(RuntimeError, "corrupt"):
            JobStore(path)
        self.assertEqual(path.read_text(), "{")
