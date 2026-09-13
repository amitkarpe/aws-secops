"""Simple authenticated-frontend operator homepage over the retained S3 worker.

Served by the same loopback service already behind ops.astromedicomp.org. The
homepage can deliberately re-arm exact demo resources after a confirmation, but
normal remediation authorization remains in LibreChat native ASK + Gateway Policy.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from http.server import HTTPServer
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .bulk import BulkStore
from .bulk_gateway import GovernedS3Provider
from .bulk_server import BulkHandler, BulkService
from .control_catalog import get_control, public_catalog
from .demo_prepare import S3_NONCOMPLIANT, count_s3, require_resettable, reset_s3
from .operator_protocol import ConfirmationGate

S3_CONTROL = "s3-bucket-level-public-access-prohibited"
SG_CONTROL = "restricted-ssh"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("internal redirects prohibited")


def _iso_mtime(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


class OperatorService(BulkService):
    def __init__(self, bulk: BulkStore, sg_origin: str = "http://localhost:4455"):
        super().__init__(bulk)
        if sg_origin != "http://localhost:4455":
            raise ValueError("SG backend must use the fixed loopback service")
        self.sg_origin = sg_origin
        self.gate = ConfirmationGate()

    def _sg(self, path: str, payload: dict | None = None) -> dict:
        url = self.sg_origin + path
        data = None if payload is None else json.dumps(payload).encode()
        headers = {"Origin": self.sg_origin, "Content-Type": "application/json"}
        request = Request(url, data=data, headers=headers)
        with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=75) as response:
            raw = response.read(200_001)
        if len(raw) > 200_000:
            raise RuntimeError("SG response too large")
        value = json.loads(raw)
        if not isinstance(value, dict) or value.get("version") != 1:
            raise RuntimeError("invalid SG response")
        return value

    def _s3_fingerprint(self) -> str:
        from .bulk import digest
        summary = self.bulk.summary()
        return digest({
            "family": "s3", "batch_id": summary.get("batch_id"), "decision": summary.get("decision"),
            "counts": summary.get("counts", {}), "manifest_hash": self.bulk.provider.context.get("manifest_hash"),
        })

    def _config_control(self, control: str) -> dict:
        summary = self._sg("/api/v1/get_config_summary")
        for item in summary.get("controls", []):
            if item.get("control") == control:
                return item
        raise RuntimeError("Config control unavailable")

    def _config_noncompliant(self, control: str) -> tuple[set[str], bool]:
        found: set[str] = set()
        partial = False
        offset = 0
        total = None
        while offset < 250:
            query = urlencode({"control": control, "status": "NON_COMPLIANT", "offset": offset, "limit": 50})
            page = self._sg("/api/v1/list_config_findings?" + query)
            total = int(page.get("total", 0))
            partial = partial or bool(page.get("partial"))
            items = page.get("items", [])
            if not isinstance(items, list) or len(items) > 50:
                raise RuntimeError("invalid Config finding page")
            found.update(str(x["resource_id"]) for x in items)
            offset += len(items)
            if not items or offset >= total:
                break
        if total is not None and len(found) < min(total, 250):
            partial = True
        return found, partial

    @staticmethod
    def _unavailable_control(family: str, title: str, action: str, message: str) -> dict:
        return {
            "version": 1, "family": family, "title": title,
            "resource_count": None, "compliant": None, "noncompliant": None, "unknown": None,
            "last_verification_time": None, "batch": None, "config": None,
            "status_available": False, "config_available": False,
            "status_error": message, "config_error": "AWS Config status unavailable",
            "action": action,
        }

    def s3_status(self) -> dict:
        summary = self.bulk.summary()
        counts = summary.get("counts", {}) if summary.get("batch_id") else {}
        total = len(self.bulk.provider.resources)
        compliant = int(summary.get("verified", 0)) if summary.get("batch_id") else 0
        noncompliant = int(counts.get("PENDING", 0) + counts.get("APPROVED", 0) + counts.get("DENIED", 0))
        unknown = max(0, total - compliant - noncompliant)
        evidence_time = None
        if self.bulk.data:
            evidence_time = (_iso_mtime(self.bulk.path) if summary.get("verified") == total
                             else self.bulk.data.get("created_at"))
        config = None
        config_available = True
        config_error = None
        try:
            config = self._config_control(S3_CONTROL)
        except Exception:
            config_available = False
            config_error = "AWS Config status unavailable"
        return {
            "version": 1, "family": "s3", "title": "S3 Block Public Access",
            "resource_count": total, "compliant": compliant, "noncompliant": noncompliant,
            "unknown": unknown, "last_verification_time": evidence_time,
            "batch": summary, "config": config,
            "status_available": True, "config_available": config_available,
            "status_error": None, "config_error": config_error,
            "action": "enable all four bucket-level Block Public Access settings",
        }

    def status(self) -> dict:
        degraded = []
        try:
            s3 = self.s3_status()
        except Exception:
            s3 = self._unavailable_control(
                "s3", "S3 Block Public Access",
                "enable all four bucket-level Block Public Access settings",
                "S3 provider/batch status unavailable",
            )
        try:
            sg = self._sg("/api/operator/sg-status")
        except Exception:
            sg = self._unavailable_control(
                "sg", "Security Group restricted SSH",
                "remove only TCP/22 ingress from 0.0.0.0/0",
                "Security Group provider/batch status unavailable",
            )
        for control in (s3, sg):
            if control.get("status_available") is False:
                degraded.append(control.get("status_error") or f"{control.get('title', control.get('family'))} status unavailable")
            if control.get("config_available") is False:
                degraded.append(control.get("config_error") or f"{control.get('title', control.get('family'))} AWS Config unavailable")
        return {
            "version": 1, "agent_url": "https://sec.astromedicomp.org/",
            "controls": [s3, sg],
            "catalog": public_catalog(),
            "degraded": bool(degraded), "degraded_sources": degraded,
            "message": ("Partial status: " + "; ".join(degraded) + ". Provider/batch truth is shown where available."
                        if degraded else "Provider verification is immediate truth; AWS Config convergence may lag."),
        }

    def prepare_preview(self, family: str) -> dict:
        if family == "sg":
            return self._sg("/api/operator/sg-prepare-preview", {})
        if family != "s3":
            raise ValueError("unsupported family")
        with self.bulk.lock:
            summary = self.bulk.summary()
            require_resettable(summary)
            fingerprint = self._s3_fingerprint()
            token = self.gate.issue("s3", fingerprint)
            return {
                "version": 1, "family": "s3", "confirmation_token": token,
                "resource_count": len(self.bulk.provider.resources),
                "action": "set BlockPublicAcls=false only; preserve other BPA flags, empty buckets, ACL-disabled ownership and no bucket policy",
                "warning": "This intentionally makes these demo buckets non-compliant. Unrelated resources are not changed.",
            }

    def prepare_demo(self, family: str, token: str) -> dict:
        if family == "sg":
            return self._sg("/api/operator/sg-prepare", {"confirmation_token": token})
        if family != "s3":
            raise ValueError("unsupported family")
        with self.bulk.lock:
            summary = self.bulk.summary()
            require_resettable(summary)
            fingerprint = self._s3_fingerprint()
            self.gate.consume(token, "s3", fingerprint)
            try:
                reset = reset_s3(self.bulk.provider)
                batch = self.bulk.preview(renew=True)
                before = [x.get("before") for x in self.bulk.data["manifest"]["resources"]]
                verified_noncompliant = sum(x == S3_NONCOMPLIANT for x in before)
            except Exception:
                provider = count_s3(self.bulk.provider)
                return {"version": 1, "status": "FAILED", "family": "s3", **provider,
                        "message": "Prepare interrupted or failed. Exact provider counts are shown; do not retry blindly."}
            if (verified_noncompliant != len(before) or batch.get("decision") != "PENDING"
                    or batch.get("counts", {}).get("PENDING") != len(before)):
                return {"version": 1, "status": "FAILED", "family": "s3",
                        "resource_count": len(before), "noncompliant": verified_noncompliant,
                        "message": "Provider reset or fresh preview did not fully verify ready."}
            return {"version": 1, "status": "DEMO_READY", "family": "s3",
                    "resource_count": len(before), "compliant": 0, "noncompliant": len(before), "unknown": 0,
                    "changed": reset["changed"], "batch_id": batch["batch_id"],
                    "message": f"DEMO READY — {len(before)} S3 buckets verified non-compliant. A fresh batch is ready. Open AWS Compliance Agent in LibreChat."}

    def s3_plan(self) -> dict:
        config_noncompliant, partial = self._config_noncompliant(S3_CONTROL)
        owned = set(self.bulk.provider.resources)
        batch = self.bulk.summary()
        direct_noncompliant: set[str] = set()
        direct_unknown = len(owned)
        if self.bulk.data and batch.get("decision") == "PENDING":
            evidence = self.bulk.data["manifest"]["resources"]
            direct_noncompliant = {x["resource"] for x in evidence if x.get("before") == S3_NONCOMPLIANT}
            direct_unknown = len(owned - direct_noncompliant)
        candidates = owned & config_noncompliant
        eligible = candidates & direct_noncompliant
        catalog = get_control(S3_CONTROL)
        return {
            "version": 1, "control": S3_CONTROL, **catalog,
            "config_noncompliant": len(config_noncompliant), "owned_resources": len(owned),
            "candidate_owned": len(candidates), "eligible_owned": len(eligible),
            "provider_evidence_unknown": direct_unknown,
            "excluded": len(config_noncompliant - owned), "partial": partial,
            "ready_to_prepare": not partial and bool(owned) and candidates == owned,
            "current_batch": batch,
            "message": ("Config identifies candidate owned resources. Existing immutable preview evidence supplies direct provider eligibility; "
                        "if absent, explicit batch preparation performs the bounded provider precondition read before any approval."),
        }

    def plan(self, control: str) -> dict:
        if control == "all":
            return {"version": 1, "control": "all", "plans": [self.s3_plan(), self._sg("/api/operator/sg-plan?control=restricted-ssh")],
                    "message": "Plan all; S3 and Security Group still require separate immutable batches and separate native approvals."}
        if control == S3_CONTROL:
            return self.s3_plan()
        if control == SG_CONTROL:
            return self._sg("/api/operator/sg-plan?control=restricted-ssh")
        raise ValueError("unsupported control")

    def prepare_batch(self, control: str) -> dict:
        if control == SG_CONTROL:
            return self._sg("/api/operator/sg-prepare-batch", {"control": SG_CONTROL})
        if control != S3_CONTROL:
            raise ValueError("one exact control required")
        plan = self.s3_plan()
        if not plan["ready_to_prepare"]:
            raise ValueError("Config evidence is not ready for the complete owned S3 batch")
        with self.bulk.lock:
            summary = self.bulk.summary()
            if self.bulk.data and summary.get("decision") == "PENDING":
                before = self.bulk.data["manifest"]["resources"]
                if all(x.get("before") == S3_NONCOMPLIANT for x in before):
                    return {"version": 1, "prepared": True, "family": "s3", "batch": summary, "reused": True}
                raise ValueError("current S3 preview does not match the exact remediation precondition")
            if self.bulk.data:
                require_resettable(summary)
                batch = self.bulk.preview(renew=True)
            else:
                batch = self.bulk.preview()
            before = self.bulk.data["manifest"]["resources"]
            if not all(x.get("before") == S3_NONCOMPLIANT for x in before):
                self.bulk.decide(batch["batch_id"], batch["approval_hash"], "REJECT")
                raise ValueError("direct S3 provider precondition does not match Config candidate scope")
            return {"version": 1, "prepared": True, "family": "s3", "batch": batch, "reused": False}


class OperatorHandler(BulkHandler):
    service: OperatorService
    operator_page = Path(__file__).with_name("static").joinpath("operator.html")

    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        if parsed.path == "/":
            if not self._local_host():
                self._json(403, {"error": "unexpected local Host"}); return
            body = self.operator_page.read_bytes()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        if parsed.path == "/api/operator/status":
            if not self._local_host():
                self._json(403, {"error": "unexpected local Host"}); return
            try: self._json(200, self.service.status())
            except Exception: self._json(503, {"error": "operator status unavailable"})
            return
        if parsed.path == "/api/operator/plan":
            if not self._local_host():
                self._json(403, {"error": "unexpected local Host"}); return
            try:
                query = parse_qs(parsed.query, strict_parsing=True)
                if set(query) != {"control"} or len(query["control"]) != 1:
                    raise ValueError("one control required")
                self._json(200, self.service.plan(query["control"][0]))
            except ValueError: self._json(400, {"error": "invalid remediation plan request"})
            except Exception: self._json(503, {"error": "remediation plan unavailable"})
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path not in {"/api/operator/prepare-preview", "/api/operator/prepare", "/api/operator/prepare-batch"}:
            super().do_POST(); return
        if not self._local_host() or not self._same_loopback_origin():
            self._json(403, {"error": "same loopback origin required"}); return
        if self.headers.get_content_type() != "application/json":
            self._json(415, {"error": "application/json required"}); return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= 4096:
                raise ValueError("invalid payload")
            data = json.loads(self.rfile.read(length))
            if self.path == "/api/operator/prepare-preview" and set(data) == {"family"}:
                result = self.service.prepare_preview(data["family"])
            elif self.path == "/api/operator/prepare" and set(data) == {"family", "confirmation_token"}:
                result = self.service.prepare_demo(data["family"], data["confirmation_token"])
            elif self.path == "/api/operator/prepare-batch" and set(data) == {"control"}:
                result = self.service.prepare_batch(data["control"])
            else:
                raise ValueError("invalid operator request")
            self._json(200, result)
        except (ValueError, RuntimeError):
            self._json(400, {"error": "operator request rejected; no automatic retry"})
        except Exception:
            self._json(503, {"error": "operator operation unavailable; inspect saved state before retry"})


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--gateway-state", type=Path, required=True)
    p.add_argument("--state", type=Path, required=True)
    p.add_argument("--port", type=int, default=4444)
    args = p.parse_args()
    if not 1024 <= args.port <= 65535:
        p.error("invalid local port")
    provider = GovernedS3Provider(args.manifest, args.gateway_state)
    store = BulkStore(args.state, provider)
    OperatorHandler.service = OperatorService(store, os.environ.get("SECOPS_SG_BACKEND_URL", "http://localhost:4455"))
    try:
        with HTTPServer(("127.0.0.1", args.port), OperatorHandler) as server:
            print(f"BULK_OPERATOR=http://localhost:{args.port}/ OPERATOR_HOME=ON MODE={provider.context['mode']}", flush=True)
            server.serve_forever()
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
