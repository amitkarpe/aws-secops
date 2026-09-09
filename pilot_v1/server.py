"""Dependency-free loopback UI for Pilot v1."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .config import PilotConfig
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
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/api/check":
                result = self.service.check()
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
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"PILOT_V1_URL=http://localhost:{server.server_port}/", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
