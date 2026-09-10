"""One-command live API smoke for the retained Pilot."""

from __future__ import annotations

import json
import argparse
from contextlib import contextmanager
import select
import subprocess
import sys
import threading
import urllib.request
import urllib.error
from http.server import HTTPServer
from pathlib import Path
from typing import Any

from .config import PilotConfig
from .server import Handler
from .service import PilotService


ROOT = Path(__file__).resolve().parents[1]


def _request(url: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(
        f"{url}{path}",
        data=body,
        headers=(
            {}
            if payload is None
            else {"Content-Type": "application/json", "Origin": url}
        ),
        method="GET" if payload is None else "POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)


def _download(url: str, path: str) -> str:
    with urllib.request.urlopen(f"{url}{path}", timeout=30) as response:
        return response.read().decode()


def _import(url: str, path: Path, source_format: str) -> dict[str, Any]:
    media_type = "text/csv" if path.suffix == ".csv" else "application/json"
    request = urllib.request.Request(
        f"{url}/api/import",
        data=path.read_bytes(),
        headers={
            "Content-Type": media_type,
            "Origin": url,
            "X-Filename": path.name,
            "X-Source-Format": source_format,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def _expect_http_error(url: str, path: str, payload: dict[str, Any], status: int) -> None:
    try:
        _request(url, path, payload)
    except urllib.error.HTTPError as exc:
        _expect(exc.code == status, f"expected HTTP {status}, received {exc.code}")
        return
    raise RuntimeError(f"expected HTTP {status}, request succeeded")


def _expect(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def run(*, specialists_only: bool = False) -> None:
    Handler.service = PilotService(PilotConfig.from_env())
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    try:
        ready = _request(url, "/api/state")
        _expect(ready.get("stage") == "READY", "app did not start in READY state")

        compliance = _import(
            url, ROOT / "examples/cloudscape-synthetic.json", "cloudscape"
        )
        _expect(
            compliance.get("audit", {}).get("specialist_route") == "Compliance Agent"
            and compliance.get("audit", {}).get("action_eligibility") == "PLAN_ONLY",
            "CloudSCAPE finding was not routed to plan-only Compliance Agent",
        )
        vulnerability = _import(url, ROOT / "examples/vapt-synthetic.csv", "vapt")
        _expect(
            vulnerability.get("audit", {}).get("specialist_route")
            == "Vulnerability Agent"
            and vulnerability.get("backlog", {}).get("total_open") == 2,
            "VAPT finding was not routed into the shared backlog",
        )
        _expect_http_error(url, "/api/approve", {"environment": "dev"}, 400)
        for state, source in [(compliance, "CloudSCAPE"), (vulnerability, "VAPT")]:
            _expect(
                state["audit"].get("explanation_tool_calls") == 0
                and state["audit"]["provider_verification"] == "NOT_PERFORMED"
                and source.lower() in state["explanation"].lower(),
                "specialist explanation lacked source grounding or zero-tool proof",
            )
            print(f"SPECIALIST={state['audit']['specialist_route']} TOOL_CALLS=0 ELIGIBILITY=PLAN_ONLY")
            print(f"EXPLANATION={state['explanation']}")
        if specialists_only:
            print("PLATFORM_SPECIALIST_SMOKE=PASS")
            return

        finding = _request(url, "/api/check", {})
        _expect(
            finding.get("finding", {}).get("status") == "NON_COMPLIANT",
            "SG finding was not NON_COMPLIANT",
        )

        rejected = _request(url, "/api/reject", {"job_id": finding["job"]["job_id"]})
        _expect(rejected.get("stage") == "REJECTED", "Reject did not complete")
        _expect(
            rejected.get("audit", {}).get("provider_verification") == "NOT_READ"
            and rejected.get("audit", {}).get("changed") is False,
            "Reject changed or lost provider state",
        )

        finding = _request(url, "/api/check", {})
        denied = _request(url, "/api/approve", {"environment": "prod", "job_id": finding["job"]["job_id"]})
        _expect(denied.get("stage") == "DENIED", "synthetic prod was not denied")
        _expect(
            denied.get("audit", {}).get("policy_decision") == "DENY"
            and denied.get("audit", {}).get("provider_verification") == "NON_COMPLIANT"
            and denied.get("audit", {}).get("changed") is False,
            "Policy DENY changed or lost provider state",
        )

        finding = _request(url, "/api/check", {})
        approved = _request(url, "/api/approve", {"environment": "dev", "job_id": finding["job"]["job_id"]})
        _expect(approved.get("stage") == "COMPLETED", "DEV approval did not complete")
        _expect(
            approved.get("audit", {}).get("policy_decision") == "ALLOW"
            and approved.get("audit", {}).get("provider_verification") == "COMPLIANT"
            and approved.get("audit", {}).get("changed") is True,
            "DEV approval did not reach provider COMPLIANT",
        )

        s3 = _request(url, "/api/check-s3", {})
        _expect(s3.get("stage") == "S3_BASELINE", "S3 baseline did not complete")
        _expect(
            s3.get("audit", {}).get("changed") is False
            and s3.get("finding", {}).get("mutation") == "none",
            "S3 baseline was not read-only",
        )
        backlog = _request(url, "/api/backlog")
        _expect(backlog.get("total_open", 0) >= 1, "backlog contains no open exception")
        csv_export = _download(url, "/api/export.csv")
        markdown_export = _download(url, "/api/export.md")
        _expect(
            "source,specialist_route,action_eligibility" in csv_export.splitlines()[0]
            and "Versioning" in csv_export,
            "CSV action plan did not contain the S3 exception",
        )
        _expect(
            markdown_export.startswith("# AWS SecOps durable action plan")
            and "Versioning" in markdown_export,
            "Markdown action plan did not contain the S3 exception",
        )
        print("PLATFORM_PHASE1_API_SMOKE=PASS")
        print(
            "PLATFORM_PHASE1_SEQUENCE=CLOUDSCAPE_IMPORT,VAPT_IMPORT,PLAN_ONLY_BLOCK,"
            "SG_FINDING,REJECT,DENY,APPROVE,S3,BACKLOG,EXPORT"
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@contextmanager
def _owned_server():
    """Restart only this smoke's child process; never take a user's listener."""
    process = subprocess.Popen(
        [sys.executable, "-m", "pilot_v1.server", "--port", "0"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
    )
    try:
        _expect(bool(select.select([process.stdout], [], [], 20)[0]), "server startup timed out")
        line = process.stdout.readline().strip()
        _expect(line.startswith("PILOT_V1_URL=http://localhost:"), "server startup failed; inspect local store/config")
        yield line.split("=", 1)[1].rstrip("/")
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        process.stdout.close()


def durable_smoke() -> None:
    with _owned_server() as url:
        first = _request(url, "/api/sync-provider", {})
        _expect(first["audit"]["explanation_tool_calls"] == 0, "unexpected specialist tool call")
        candidates = [item for item in first["backlog"]["open_findings"] if item["source"] == "AWS Config"
                      and item["seen_in_latest_sync"] and item["planning_status"] == "UNPLANNED"
                      and not item["owner"] and not item["mitigation_plan"] and not item["target"]]
        _expect(bool(candidates), "no unplanned real Config finding; existing operator work preserved")
        item = candidates[0]
        identity = item["finding_id"]
        plan = dict(finding_id=identity, owner="Lab operator", mitigation_plan="Review recorded Config evidence before a separately approved change.", target="next lab review", planning_status="PLANNED")
        saved = _request(url, "/api/plan", plan)
        _expect(saved["backlog"]["planned"] >= 1, "plan was not saved")
        _expect_http_error(url, "/api/approve", {"environment": "dev"}, 400)
    with _owned_server() as url:
        recovered = _request(url, "/api/backlog")
        restored = next(f for f in recovered["open_findings"] if f["finding_id"] == identity)
        _expect(all(restored[key] == value for key, value in plan.items()), "restart lost the plan")
        result = _request(url, "/api/sync-provider", {})
        latest = next(f for f in result["backlog"]["open_findings"] if f["finding_id"] == identity)
        _expect(all(latest[key] == value for key, value in plan.items()), "sync changed operator plan")
        _expect(latest["first_seen"] == item["first_seen"] and latest["last_seen"] >= item["last_seen"]
                and latest["occurrence_count"] == item["occurrence_count"] + 1 and latest["seen_in_latest_sync"], "tracking did not reconcile")
        _expect(latest["action_eligibility"] == "PLAN_ONLY" and result["audit"]["explanation_tool_calls"] == 0, "boundary changed")
        _expect_http_error(url, "/api/approve", {"environment": "dev"}, 400)
        for path in ("/api/export.csv", "/api/export.md"):
            exported = _download(url, path)
            _expect(identity in exported and plan["mitigation_plan"] in exported and "PLANNED" in exported, "export lost identity or plan")
        print("PLATFORM_PHASE3_DURABLE_SMOKE=PASS")
        print(f"SOURCE=AWS_CONFIG COUNT={result['source_status']['count']} RESTART=PASS PLAN_RETAINED=PASS TRACKING=PASS EXPORT=PASS TOOLS=0 AWS_MUTATIONS=0")


def jobs_smoke() -> None:
    completed = []
    with _owned_server() as url:
        for decision, expected in (("REJECT", "REJECTED"), ("DENY_TEST", "DENIED"), ("APPROVE", "COMPLETED")):
            checked = _request(url, "/api/check", {})
            _expect(checked["finding"]["status"] == "NON_COMPLIANT", "demo must start noncompliant")
            job = checked["job"]
            _expect(job["state"] == "PENDING" and job["action"] == "remove_unrestricted_ssh" and job["environment"] == "dev", "incorrect job preview")
            result = _request(url, "/api/jobs/decision", {"job_id": job["job_id"], "decision": decision})["job"]
            _expect(result["state"] == expected, "job did not reach expected terminal state")
            _expect(result["changed"] is (decision == "APPROVE"), "unexpected change evidence")
            if decision == "REJECT":
                _expect(result["policy_decision"] == "NOT_CALLED", "Reject called Policy")
            else:
                _expect(result["policy_decision"] == ("ALLOW" if decision == "APPROVE" else "DENY"), "wrong Policy decision")
                _expect(result["provider_after"] == ("COMPLIANT" if decision == "APPROVE" else "NON_COMPLIANT"), "provider verification failed")
            _expect_http_error(url, "/api/jobs/decision", {"job_id": job["job_id"], "decision": "APPROVE"}, 400)
            completed.append(result)
            print(f"JOB={expected} REPLAY=BLOCKED POLICY={result['policy_decision']} CHANGED={result['changed']} PROVIDER_AFTER={result['provider_after']}")
    with _owned_server() as url:
        history = _request(url, "/api/jobs")["jobs"]
        for job in completed:
            _expect(next(item for item in history if item["job_id"] == job["job_id"]) == job, "restart changed audit history")
        _expect_http_error(url, "/api/jobs/decision", {"job_id": completed[-1]["job_id"], "decision": "APPROVE"}, 400)
    print("PLATFORM_PHASE4_JOBS_SMOKE=PASS RESTART=PASS NO_AUTOMATIC_REPLAY=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--specialists-only", action="store_true")
    parser.add_argument("--provider-only", action="store_true")
    parser.add_argument("--durable-only", action="store_true")
    parser.add_argument("--jobs-only", action="store_true")
    parser.add_argument("--port", type=int, default=3340)
    args = parser.parse_args()
    if args.jobs_only:
        jobs_smoke()
    elif args.durable_only:
        durable_smoke()
    elif args.provider_only:
        url = f"http://localhost:{args.port}"
        result = _request(url, "/api/sync-provider", {})
        finding = result.get("finding") or {}
        _expect(finding.get("source") == "AWS Config", "no real Config finding returned")
        _expect(finding.get("evidence_origin") == "AWS_PROVIDER", "missing provider provenance")
        _expect(finding.get("action_eligibility") == "PLAN_ONLY", "unexpected mutation eligibility")
        _expect(result["audit"].get("explanation_tool_calls") == 0, "specialist attempted a tool")
        _expect("config" in result["explanation"].lower(), "explanation omitted provider source")
        _expect(result["source_status"].get("last_success") is not None, "missing sync time")
        _expect_http_error(url, "/api/approve", {"environment": "dev"}, 400)
        for path in ["/api/export.csv", "/api/export.md"]:
            exported = _download(url, path)
            _expect(finding["resource_id"] in exported and "AWS_PROVIDER" in exported,
                    "export did not retain provider finding/provenance")
        print("PLATFORM_PHASE2_PROVIDER_SMOKE=PASS")
        print(f"SOURCE=AWS_CONFIG STATUS={result['source_status']['status']} COUNT={result['source_status']['count']} TOOLS=0 ELIGIBILITY=PLAN_ONLY")
    else:
        run(specialists_only=args.specialists_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
