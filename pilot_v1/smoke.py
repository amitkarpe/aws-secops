"""One-command live API smoke for the retained Pilot."""

from __future__ import annotations

import json
import threading
import urllib.request
from http.server import HTTPServer
from typing import Any

from .config import PilotConfig
from .server import Handler
from .service import PilotService


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


def _expect(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def run() -> None:
    Handler.service = PilotService(PilotConfig.from_env())
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    try:
        ready = _request(url, "/api/state")
        _expect(ready.get("stage") == "READY", "app did not start in READY state")

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
        print("PILOT_V1_1_API_SMOKE=PASS")
        print("PILOT_V1_1_SEQUENCE=SG_FINDING,REJECT,DENY,APPROVE,S3")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def main() -> int:
    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
