"""Dependency-free loopback UI for Pilot v1."""

from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

from .config import PilotConfig
from .findings import MAX_IMPORT_BYTES
from .service import PilotService


class Handler(BaseHTTPRequestHandler):
    service: PilotService
    page = Path(__file__).with_name("static").joinpath("index.html")

    def setup(self) -> None:
        super().setup()
        # Browser-preopened idle sockets must not pin this single-writer server.
        self.connection.settimeout(5)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _json(self, status: int, value: object) -> None:
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _download(self, media_type: str, filename: str, value: str) -> None:
        body = value.encode()
        self.send_response(200)
        self.send_header("Content-Type", media_type)
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _same_loopback_origin(self) -> bool:
        host = urlsplit(f"//{self.headers.get('Host', '')}")
        origin = urlsplit(self.headers.get("Origin", ""))
        port = self.server.server_port
        allowed_hosts = {"localhost", "127.0.0.1"}
        return (
            host.hostname in allowed_hosts
            and host.port == port
            and origin.scheme == "http"
            and origin.hostname == host.hostname
            and origin.port == host.port
            and not origin.path
            and not origin.query
            and not origin.fragment
        )

    def _local_host(self) -> bool:
        try:
            return self.headers.get_all("Host") in ([f"localhost:{self.server.server_port}"],
                                                     [f"127.0.0.1:{self.server.server_port}"])
        except ValueError:
            return False

    def do_GET(self) -> None:
        if not self._local_host():
            self._json(403, {"error": "unexpected local Host"})
            return
        parsed = urlsplit(self.path)
        if parsed.path.startswith("/api/v1/"):
            try:
                query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True, max_num_fields=5)
                if any(len(value) != 1 for value in query.values()):
                    raise ValueError("duplicate argument")
                arguments = {key: value[0] for key, value in query.items()}
                for key in ("limit", "offset"):
                    if key in arguments:
                        arguments[key] = int(arguments[key])
                operation = parsed.path.removeprefix("/api/v1/")
                if operation == "explain_finding":
                    raise ValueError("explanation requires explicit POST")
                self._json(200, self.service.query(operation, arguments))
            except ValueError:
                self._json(400, {"error": "invalid query, filter or unknown ID"})
            except Exception:
                self._json(503, {"error": "backend unavailable; no action performed"})
        elif parsed.path == "/":
            body = self.page.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif parsed.path == '/bulk':
            body = self.page.with_name('bulk.html').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers(); self.wfile.write(body)
        elif parsed.path == '/api/bulk/export':
            try:
                query = parse_qs(parsed.query, strict_parsing=True)
                if set(query) != {'batch_id'} or len(query['batch_id']) != 1 or not self.service.bulk:
                    raise ValueError('invalid batch')
                self._download('text/csv; charset=utf-8', 'batch-results.csv', self.service.bulk.export(query['batch_id'][0]))
            except ValueError:
                self._json(400, {'error': 'unknown batch'})
        elif self.path == "/api/state":
            self._json(200, self.service.state)
        elif self.path == "/api/backlog":
            self._json(200, self.service.backlog())
        elif self.path == "/api/jobs":
            self._json(200, {"jobs": self.service.jobs.history()})
        elif self.path == "/api/export.csv":
            self._download("text/csv; charset=utf-8", "platform-phase1-action-plan.csv", self.service.export_csv())
        elif self.path == "/api/export.md":
            self._download("text/markdown; charset=utf-8", "platform-phase1-action-plan.md", self.service.export_markdown())
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        try:
            if not self._local_host():
                self._json(403, {"error": "unexpected local Host"})
                return
            if self.path != "/api/import" and self.headers.get_content_type() != "application/json":
                self._json(415, {"error": "POST requires application/json"})
                return
            if not self._same_loopback_origin():
                self._json(403, {"error": "POST requires the same loopback origin"})
                return
            length = int(self.headers.get("Content-Length", "0"))
            if self.path == "/api/import":
                if self.headers.get_content_type() not in {"application/json", "text/csv"}:
                    self._json(415, {"error": "import requires JSON or CSV content"})
                    return
                if length < 1 or length > MAX_IMPORT_BYTES:
                    raise ValueError("finding import must be between 1 byte and 256 KB")
                filename = self.headers.get("X-Filename", "")
                if (
                    not filename
                    or Path(filename).name != filename
                    or "\\" in filename
                ):
                    raise ValueError("import filename must not contain a filesystem path")
                result = self.service.import_source(
                    self.rfile.read(length),
                    filename,
                    self.headers.get("X-Source-Format", ""),
                )
                self._json(200, result)
                return
            if length < 0 or length > 16_000:
                raise ValueError("JSON action exceeds 16 KB")
            payload = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(payload, dict):
                raise ValueError("JSON action must be an object")
            if self.path.startswith('/api/bulk/'):
                bulk = self.service.bulk
                if not bulk:
                    raise ValueError('bulk provider not configured')
                operation = self.path.removeprefix('/api/bulk/')
                fields = {'preview': set(), 'new-preview': set(), 'decision': {'batch_id', 'approval_hash', 'decision'},
                          'step': {'batch_id'}, 'reconcile': {'batch_id'}}
                if operation not in fields or set(payload) != fields[operation]:
                    raise ValueError('only exact server-owned bulk parameters accepted')
                if operation in {'preview', 'new-preview'}:
                    result = bulk.preview(renew=operation == 'new-preview')
                elif operation == 'decision':
                    result = bulk.decide(**payload)
                else:
                    result = getattr(bulk, operation)(**payload)
            elif self.path == "/api/v1/explain_finding":
                result = self.service.query("explain_finding", payload)
            elif self.path == "/api/sync-provider":
                if payload != {}:
                    raise ValueError("AWS Config sync accepts no caller parameters")
                result = self.service.sync_provider()
            elif self.path == "/api/check":
                result = self.service.check()
            elif self.path == "/api/plan":
                result = self.service.update_plan(payload)
            elif self.path == "/api/jobs":
                if set(payload) != {"finding_id"}:
                    raise ValueError("job creation accepts only an existing finding_id")
                result = self.service.create_job(payload["finding_id"])
            elif self.path == "/api/jobs/decision":
                if set(payload) != {"job_id", "decision"}:
                    raise ValueError("job decision accepts only job_id and decision")
                result = self.service.decide_job(payload["job_id"], payload["decision"])
            elif self.path == "/api/check-s3":
                result = self.service.check_s3()
            elif self.path == "/api/reject":
                if set(payload) != {"job_id"}:
                    raise ValueError("Reject requires the exact job_id")
                result = self.service.decide_job(payload["job_id"], "REJECT")
            elif self.path == "/api/approve":
                if set(payload) != {"job_id", "environment"} or payload["environment"] not in {"dev", "prod"}:
                    raise ValueError("Approve requires exact job_id and dev or synthetic prod")
                result = self.service.decide_job(payload["job_id"], "APPROVE" if payload["environment"] == "dev" else "DENY_TEST")
            else:
                self._json(404, {"error": "not found"})
                return
            self._json(200, result)
        except (ValueError, RuntimeError, json.JSONDecodeError) as exc:
            self._json(400, {"error": "Request rejected or operation failed; check input, source health and local store readiness. No automatic retry."})
        except Exception:
            self._json(503, {"error": "Operation unavailable; check saved job outcome before retrying any action."})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3340)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost"}:
        parser.error("Pilot v1 binds to loopback only")
    backlog_path = os.environ.get("PILOT_BACKLOG_FILE", str(Path.home() / ".local/state/aws-secops/backlog.json"))
    Handler.service = PilotService(PilotConfig.from_env(), backlog_path=backlog_path)
    if os.environ.get('SECOPS_BULK_STATE'):
        from .bulk import BulkStore, OfflineProvider
        bulk_path = os.environ['SECOPS_BULK_STATE']
        if os.environ.get('SECOPS_BULK_MANIFEST'):
            from .bulk_s3 import S3Provider
            provider = S3Provider(os.environ['SECOPS_BULK_MANIFEST'])
        else:
            provider = OfflineProvider(bulk_path+'.provider.json')
        Handler.service.bulk = BulkStore(bulk_path, provider)
    server = HTTPServer((args.host, args.port), Handler)
    print(f"PILOT_V1_URL=http://localhost:{server.server_port}/", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
