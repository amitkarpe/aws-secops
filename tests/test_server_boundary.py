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

    def approve(self, environment):
        self.approve_calls += 1
        return {"stage": "COMPLETED", "environment": environment}


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

    def post(self, content_type, origin):
        request = urllib.request.Request(
            self.url,
            data=json.dumps({"environment": "dev"}).encode(),
            headers={"Content-Type": content_type, "Origin": origin},
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


if __name__ == "__main__":
    unittest.main()
