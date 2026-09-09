"""One-command live API smoke for the retained Pilot."""

from __future__ import annotations

import json
import argparse
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

        rejected = _request(url, "/api/reject", {})
        _expect(rejected.get("stage") == "REJECTED", "Reject did not complete")
        _expect(
            rejected.get("audit", {}).get("provider_verification") == "NON_COMPLIANT"
            and rejected.get("audit", {}).get("changed") is False,
            "Reject changed or lost provider state",
        )

        denied = _request(url, "/api/approve", {"environment": "prod"})
        _expect(denied.get("stage") == "DENIED", "synthetic prod was not denied")
        _expect(
            denied.get("audit", {}).get("policy_decision") == "DENY"
            and denied.get("audit", {}).get("provider_verification") == "NON_COMPLIANT"
            and denied.get("audit", {}).get("changed") is False,
            "Policy DENY changed or lost provider state",
        )

        approved = _request(url, "/api/approve", {"environment": "dev"})
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
            csv_export.startswith("source,specialist_route,action_eligibility")
            and "Versioning" in csv_export,
            "CSV action plan did not contain the S3 exception",
        )
        _expect(
            markdown_export.startswith("# AWS SecOps Platform Phase 1 action plan")
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--specialists-only", action="store_true")
    parser.add_argument("--provider-only", action="store_true")
    parser.add_argument("--port", type=int, default=3340)
    args = parser.parse_args()
    if args.provider_only:
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
