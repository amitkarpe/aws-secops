import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import HTTPServer

from pilot_v1.server import Handler


class FakeService:
    state = {"stage": "READY"}

    def __init__(self):
        self.approve_calls = 0
        self.import_calls = 0
        self.sync_calls = 0
        self.plan_calls = 0

    def update_plan(self, payload):
        self.plan_calls += 1
        return {"stage": "READY"}

    def approve(self, environment):
        self.approve_calls += 1
        return {"stage": "COMPLETED", "environment": environment}

    def decide_job(self, job_id, decision):
        self.approve_calls += 1
        return {"stage": "COMPLETED"}

    def import_source(self, content, filename, source_format):
        self.import_calls += 1
        return {
            "stage": "IMPORTED",
            "bytes": len(content),
            "filename": filename,
            "source_format": source_format,
        }

    def sync_provider(self):
        self.sync_calls += 1
        return {"stage": "SOURCE_SYNCED"}


class ServerBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.service = FakeService()
        Handler.service = self.service
        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_port
        self.url = f"http://127.0.0.1:{self.port}/api/approve"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def post(self, content_type, origin, *, path="approve", body=None, headers=None):
        request = urllib.request.Request(
            self.url.rsplit("/", 1)[0] + f"/{path}",
            data=body or json.dumps({"environment": "dev", "job_id": "synthetic"}).encode(),
            headers={"Content-Type": content_type, "Origin": origin, **(headers or {})},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request) as response:
                return response.status
        except urllib.error.HTTPError as exc:
            return exc.code

    def test_only_same_origin_json_reaches_approval(self):
        self.assertEqual(self.post("text/plain", "https://attacker.example"), 415)
        self.assertEqual(self.service.approve_calls, 0)

        self.assertEqual(self.post("application/json", "https://attacker.example"), 403)
        self.assertEqual(self.service.approve_calls, 0)

        self.assertEqual(
            self.post("application/json; charset=utf-8", f"http://127.0.0.1:{self.port}"),
            200,
        )
        self.assertEqual(self.service.approve_calls, 1)

    def test_reads_reject_external_host_and_unknown_queries(self):
        for path, headers, status in [("/api/state", {"Host": "attacker.example"}, 403),
                                      ("/", {"Host": "localhost"}, 403),
                                      ("/api/v1/get_finding?finding_id=a&finding_id=b", {}, 400),
                                      ("/api/v1/explain_finding?finding_id=a", {}, 400)]:
            request = urllib.request.Request(f"http://127.0.0.1:{self.port}" + path, headers=headers)
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(request)
            self.assertEqual(error.exception.code, status)
        self.assertEqual(self.service.approve_calls, 0)

    def test_import_accepts_content_but_rejects_paths_and_wrong_origin(self):
        body = b'{"findings": []}'
        origin = f"http://127.0.0.1:{self.port}"
        headers = {"X-Filename": "sample.json", "X-Source-Format": "cloudscape"}
        self.assertEqual(
            self.post("application/json", origin, path="import", body=body, headers=headers),
            200,
        )
        self.assertEqual(self.service.import_calls, 1)

        path_headers = dict(headers, **{"X-Filename": "/tmp/private.json"})
        self.assertEqual(
            self.post("application/json", origin, path="import", body=body, headers=path_headers),
            400,
        )
        self.assertEqual(
            self.post(
                "application/json",
                "https://attacker.example",
                path="import",
                body=body,
                headers=headers,
            ),
            403,
        )
        self.assertEqual(self.service.import_calls, 1)

    def test_provider_sync_rejects_caller_selection(self):
        origin = f"http://127.0.0.1:{self.port}"
        self.assertEqual(self.post("application/json", origin, path="sync-provider",
                                   body=b'{"region":"other"}'), 400)
        self.assertEqual(self.service.sync_calls, 0)
        self.assertEqual(self.post("application/json", origin, path="sync-provider", body=b'{}'), 200)
        self.assertEqual(self.service.sync_calls, 1)

    def test_planning_has_same_origin_json_and_size_boundary(self):
        origin = f"http://127.0.0.1:{self.port}"
        self.assertEqual(self.post("text/plain", origin, path="plan"), 415)
        self.assertEqual(self.post("application/json", "https://attacker.example", path="plan"), 403)
        self.assertEqual(self.post("application/json", origin, path="plan", body=b"x" * 16_001), 400)
        self.assertEqual(self.post("application/json", origin, path="plan", body=b"[]"), 400)
        self.assertEqual(self.service.plan_calls, 0)
        self.assertEqual(self.post("application/json", origin, path="plan", body=b"{}"), 200)
        self.assertEqual(self.service.plan_calls, 1)


if __name__ == "__main__":
    unittest.main()
