"""Dependency-free loopback UI for Pilot v1."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .config import PilotConfig
from .findings import MAX_IMPORT_BYTES
from .service import PilotService


class Handler(BaseHTTPRequestHandler):
    service: PilotService
    page = Path(__file__).with_name("static").joinpath("index.html")

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

    def do_GET(self) -> None:
        if self.path == "/":
            body = self.page.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/state":
            self._json(200, self.service.state)
        elif self.path == "/api/backlog":
            self._json(200, self.service.backlog())
        elif self.path == "/api/export.csv":
            self._download("text/csv; charset=utf-8", "platform-phase1-action-plan.csv", self.service.export_csv())
        elif self.path == "/api/export.md":
            self._download("text/markdown; charset=utf-8", "platform-phase1-action-plan.md", self.service.export_markdown())
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        try:
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
            payload = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/api/sync-provider":
                if payload != {}:
                    raise ValueError("AWS Config sync accepts no caller parameters")
                result = self.service.sync_provider()
            elif self.path == "/api/check":
                result = self.service.check()
            elif self.path == "/api/check-s3":
                result = self.service.check_s3()
            elif self.path == "/api/reject":
                result = self.service.reject()
            elif self.path == "/api/approve":
                result = self.service.approve(payload.get("environment", ""))
            else:
                self._json(404, {"error": "not found"})
                return
            self._json(200, result)
        except (ValueError, RuntimeError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3340)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost"}:
        parser.error("Pilot v1 binds to loopback only")
    Handler.service = PilotService(PilotConfig.from_env())
    server = HTTPServer((args.host, args.port), Handler)
    print(f"PILOT_V1_URL=http://localhost:{server.server_port}/", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
