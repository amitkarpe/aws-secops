"""Operator-only extensions for the governed SG worker.

The normal remediation path remains native LibreChat ASK -> Gateway Policy ->
exact Lambda. These endpoints only support read-only planning and deliberate demo
re-arm; they are loopback-only and are not exposed as MCP mutation tools.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from http.server import HTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .control_catalog import get_control
from .demo_prepare import SG_NONCOMPLIANT, count_sg, require_resettable, reset_sg
from .operator_protocol import ConfirmationGate
from .sg_compliance import ConfigComplianceReader, GovernedSGProvider, Handler, SGBatchStore, Service, digest

CONTROL = "restricted-ssh"


class OperatorSGService(Service):
    def __init__(self, store: SGBatchStore, config: ConfigComplianceReader):
        super().__init__(store, config)
        self.gate = ConfirmationGate()

    def _fingerprint(self) -> str:
        summary = self.store.summary()
        return digest({
            "family": "sg", "batch_id": summary.get("batch_id"), "decision": summary.get("decision"),
            "counts": summary.get("counts", {}), "manifest_hash": self.store.provider.context.get("manifest_hash"),
        })

    def status(self) -> dict:
        summary = self.store.summary()
        provider = count_sg(self.store.provider)
        config_control = None
        config_available = True
        config_error = None
        try:
            config_summary = self.config.summary()
            config_control = next(x for x in config_summary["controls"] if x["control"] == CONTROL)
        except Exception:
            config_available = False
            config_error = "AWS Config status unavailable"
        return {
            "version": 1, "family": "sg", "title": "Security Group restricted SSH",
            "resource_count": provider["total"], "compliant": provider["compliant"],
            "noncompliant": provider["noncompliant"], "unknown": provider["unknown"],
            "last_verification_time": datetime.now(timezone.utc).isoformat(),
            "batch": summary, "config": config_control,
            "status_available": True, "config_available": config_available,
            "status_error": None, "config_error": config_error,
            "action": "remove only TCP/22 ingress from 0.0.0.0/0",
        }

    def plan(self) -> dict:
        rows, partial = self.config._results(CONTROL)
        config_noncompliant = {str(x["resource_id"]) for x in rows if x["status"] == "NON_COMPLIANT"}
        owned = set(self.store.provider.resources)
        provider_noncompliant = {r for r in owned if self.store.provider.read(r) == SG_NONCOMPLIANT}
        eligible = owned & config_noncompliant & provider_noncompliant
        outside = config_noncompliant - owned
        catalog = get_control(CONTROL)
        return {
            "version": 1, "control": CONTROL, **catalog,
            "config_noncompliant": len(config_noncompliant), "owned_resources": len(owned),
            "eligible_owned": len(eligible), "excluded": len(outside) + len(provider_noncompliant - config_noncompliant),
            "partial": partial, "ready_to_prepare": not partial and bool(owned) and eligible == owned,
            "current_batch": self.store.summary(),
            "message": "Eligibility requires Config NON_COMPLIANT + exact owned manifest + direct EC2 precondition.",
        }

    def prepare_batch(self) -> dict:
        with self.store.lock:
            plan = self.plan()
            if not plan["ready_to_prepare"]:
                raise ValueError("SG evidence is not ready for one exact owned batch")
            summary = self.store.summary()
            if summary.get("decision") == "PENDING" and summary.get("counts", {}).get("PENDING") == len(self.store.provider.resources):
                return {"version": 1, "prepared": True, "family": "sg", "batch": summary, "reused": True}
            if self.store.data:
                require_resettable(summary)
                batch = self.store.preview(renew=True)
            else:
                batch = self.store.preview()
            if batch.get("decision") != "PENDING" or batch.get("counts", {}).get("PENDING") != len(self.store.provider.resources):
                raise RuntimeError("fresh SG batch was not safely prepared")
            return {"version": 1, "prepared": True, "family": "sg", "batch": batch, "reused": False}

    def prepare_preview(self) -> dict:
        with self.store.lock:
            summary = self.store.summary()
            require_resettable(summary)
            provider = count_sg(self.store.provider)
            fingerprint = self._fingerprint()
            token = self.gate.issue("sg", fingerprint)
            return {
                "version": 1, "family": "sg", "confirmation_token": token,
                "resource_count": provider["total"],
                "action": "restore only TCP/22 from 0.0.0.0/0 on exact owned unattached demo Security Groups",
                "warning": "This intentionally makes these demo Security Groups non-compliant. Unrelated resources are not changed.",
            }

    def prepare_demo(self, token: str) -> dict:
        with self.store.lock:
            summary = self.store.summary()
            require_resettable(summary)
            fingerprint = self._fingerprint()
            self.gate.consume(token, "sg", fingerprint)
            try:
                reset = reset_sg(self.store.provider)
                provider = count_sg(self.store.provider)
                if provider["noncompliant"] != provider["total"]:
                    return {"version": 1, "status": "FAILED", "family": "sg", **provider,
                            "message": "Reset did not verify every owned Security Group; no fresh batch claimed ready."}
                batch = self.store.preview(renew=True)
            except Exception:
                provider = count_sg(self.store.provider)
                return {"version": 1, "status": "FAILED", "family": "sg", **provider,
                        "message": "Prepare interrupted or failed. Exact provider counts are shown; do not retry blindly."}
            if batch.get("decision") != "PENDING" or batch.get("counts", {}).get("PENDING") != provider["total"]:
                return {"version": 1, "status": "FAILED", "family": "sg", **provider,
                        "message": "Provider reset succeeded but fresh batch preparation did not verify ready."}
            return {"version": 1, "status": "DEMO_READY", "family": "sg", **provider,
                    "changed": reset["changed"], "batch_id": batch["batch_id"],
                    "message": f"DEMO READY — {provider['total']} Security Groups verified non-compliant. A fresh batch is ready. Open AWS Compliance Agent in LibreChat."}


class OperatorHandler(Handler):
    service: OperatorSGService

    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        if parsed.path == "/api/operator/sg-status":
            if not self._host_ok():
                self._json(403, {"error": "unexpected local Host"}); return
            try:
                self._json(200, self.service.status())
            except Exception:
                self._json(503, {"error": "SG operator status unavailable"})
            return
        if parsed.path == "/api/operator/sg-plan":
            if not self._host_ok():
                self._json(403, {"error": "unexpected local Host"}); return
            try:
                query = parse_qs(parsed.query, strict_parsing=True)
                if query not in ({}, {"control": [CONTROL]}):
                    raise ValueError("unsupported control")
                self._json(200, self.service.plan())
            except ValueError:
                self._json(400, {"error": "invalid SG plan request"})
            except Exception:
                self._json(503, {"error": "SG plan unavailable"})
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path not in {"/api/operator/sg-prepare-preview", "/api/operator/sg-prepare", "/api/operator/sg-prepare-batch"}:
            super().do_POST(); return
        if not self._host_ok() or not self._origin_ok():
            self._json(403, {"error": "same loopback origin required"}); return
        if self.headers.get_content_type() != "application/json":
            self._json(415, {"error": "application/json required"}); return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 <= length <= 4096:
                raise ValueError("payload too large")
            data = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/api/operator/sg-prepare-preview" and data == {}:
                result = self.service.prepare_preview()
            elif self.path == "/api/operator/sg-prepare" and set(data) == {"confirmation_token"}:
                result = self.service.prepare_demo(data["confirmation_token"])
            elif self.path == "/api/operator/sg-prepare-batch" and data in ({}, {"control": CONTROL}):
                result = self.service.prepare_batch()
            else:
                raise ValueError("invalid SG operator request")
            self._json(200, result)
        except (ValueError, RuntimeError):
            self._json(400, {"error": "SG operator request rejected; no automatic retry"})
        except Exception:
            self._json(503, {"error": "SG operator operation unavailable"})


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--gateway-state", type=Path, required=True)
    p.add_argument("--state", type=Path, required=True)
    p.add_argument("--port", type=int, default=4455)
    args = p.parse_args()
    if not 1024 <= args.port <= 65535:
        p.error("invalid loopback port")
    provider = GovernedSGProvider(args.manifest, args.gateway_state)
    store = SGBatchStore(args.state, provider)
    OperatorHandler.service = OperatorSGService(store, ConfigComplianceReader())
    try:
        with HTTPServer(("127.0.0.1", args.port), OperatorHandler) as server:
            print(f"SG_COMPLIANCE=http://localhost:{args.port} COUNT={len(provider.resources)} OPERATOR_EXTENSIONS=ON", flush=True)
            server.serve_forever()
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
