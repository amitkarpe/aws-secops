"""Bounded local job journal; no execution or automatic retries on load."""

import json
import os
from pathlib import Path
import tempfile
from uuid import uuid4

from .backlog import _now

MAX_JOBS = 100
STATES = {"PENDING", "EXECUTING", "REJECTED", "DENIED", "COMPLETED", "FAILED"}
FIELDS = {"job_id", "finding_id", "resource_id", "resource_name", "control", "evidence",
          "created_at", "completed_at", "action", "environment", "expected_postcondition",
          "state", "human_decision", "policy_decision", "provider_before", "provider_after",
          "changed", "message"}


class JobStore:
    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self.jobs = {}
        if self.path is None:
            return
        try:
            with self.path.open("rb") as stream:
                raw = stream.read(256_001)
        except FileNotFoundError:
            return
        except OSError as exc:
            raise RuntimeError("Job store unreadable; startup stopped.") from exc
        try:
            data = json.loads(raw)
            if len(raw) > 256_000 or data.get("version") != 1 or not isinstance(data.get("jobs"), list) or len(data["jobs"]) > MAX_JOBS:
                raise ValueError("invalid job store")
            for job in data["jobs"]:
                if not isinstance(job, dict) or set(job) != FIELDS or job.get("state") not in STATES or job.get("action") != "remove_unrestricted_ssh" or job.get("environment") != "dev":
                    raise ValueError("invalid stored job")
                if any(not isinstance(job[key], str) or len(job[key]) > 1000 for key in FIELDS - {"changed", "completed_at"}):
                    raise ValueError("invalid job fields")
                if job["changed"] is not None and type(job["changed"]) is not bool:
                    raise ValueError("invalid change evidence")
                if job["state"] == "PENDING" and (job["human_decision"] != "PENDING" or job["policy_decision"] != "NOT_CALLED" or job["changed"] is not False):
                    raise ValueError("invalid pending decision")
                if len(job["job_id"]) != 32 or len(job["finding_id"]) != 64 or job["job_id"] in self.jobs:
                    raise ValueError("invalid job identity")
                self.jobs[job["job_id"]] = job
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise RuntimeError("Job store corrupt; startup stopped without overwriting it.") from exc
        # A crash can occur after dispatch but before result persistence.
        # Never infer a no-change result or repeat that dispatch.
        recovered = dict(self.jobs)
        for key, job in self.jobs.items():
            if job["state"] == "EXECUTING":
                recovered[key] = dict(job, state="FAILED", completed_at=_now(), changed=None,
                                      message="Interrupted execution; outcome unknown. Recheck provider; no automatic retry.")
        if recovered != self.jobs:
            self._save(recovered)

    def _save(self, jobs):
        data = json.dumps({"version": 1, "jobs": list(jobs.values())}).encode()
        if len(jobs) > MAX_JOBS or len(data) > 256_000:
            raise ValueError("Job history limit reached; existing jobs retained.")
        if self.path:
            temporary = None
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(dir=self.path.parent, prefix=".jobs-", delete=False) as stream:
                    temporary = stream.name
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, self.path)
            except OSError as exc:
                raise RuntimeError("Job save failed; no further execution permitted.") from exc
            finally:
                if temporary and os.path.exists(temporary):
                    os.unlink(temporary)
        self.jobs = jobs

    def create(self, finding):
        for job in self.jobs.values():
            if job["finding_id"] == finding["finding_id"] and job["state"] in {"PENDING", "EXECUTING"}:
                return dict(job)
        job = dict(job_id=uuid4().hex, finding_id=finding["finding_id"],
                   resource_id=finding["resource_id"], resource_name=finding["resource_name"],
                   control=finding["control"], evidence=finding["evidence"],
                   created_at=_now(), completed_at=None, action="remove_unrestricted_ssh",
                   environment="dev", expected_postcondition="COMPLIANT: exact public TCP/22 rule absent",
                   state="PENDING", human_decision="PENDING", policy_decision="NOT_CALLED",
                   provider_before=finding["status"], provider_after="NOT_READ", changed=False,
                   message="Review the exact DEV action. A mitigation plan is not approval.")
        self._save({**self.jobs, job["job_id"]: job})
        return dict(job)

    def get(self, job_id):
        if not isinstance(job_id, str) or job_id not in self.jobs:
            raise ValueError("unknown server-owned job ID")
        return dict(self.jobs[job_id])

    def update(self, job_id, **values):
        job = dict(self.get(job_id), **values)
        self._save({**self.jobs, job_id: job})
        return job

    def history(self):
        return [dict(job) for job in reversed(list(self.jobs.values()))]
