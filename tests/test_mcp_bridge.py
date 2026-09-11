"""Protocol-level boundary tests using the pinned optional official SDK."""
import importlib.util
import unittest
from unittest.mock import patch


@unittest.skipUnless(importlib.util.find_spec("mcp"), "install requirements-mcp.txt for MCP boundary tests")
class McpBoundaryTest(unittest.IsolatedAsyncioTestCase):
    def test_review_origin_is_display_only_and_https(self):
        from pilot_v1.mcp_bridge import review_origin, backend_url
        with patch.dict('os.environ', {'SECOPS_REVIEW_ORIGIN': 'https://ops.example.test',
                                     'SECOPS_BACKEND_URL': 'http://localhost:3340'}):
            self.assertEqual(review_origin(backend_url()), 'https://ops.example.test')
            self.assertEqual(backend_url(), 'http://localhost:3340')
        for value in ['http://ops.example.test', 'https://user:pass@ops.example.test',
                      'https://ops.example.test/path', 'https://ops.example.test:444',
                      'https://ops.example.test?redirect=x']:
            with patch.dict('os.environ', {'SECOPS_REVIEW_ORIGIN': value}):
                with self.assertRaises(ValueError):
                    review_origin('http://localhost:3340')

    async def test_only_six_tools_reject_extra_args_unknown_tools_and_paths(self):
        from pilot_v1.mcp_bridge import server, dispatch, OPERATIONS
        tools = await server.list_tools()
        self.assertEqual({t.name for t in tools}, OPERATIONS)
        self.assertTrue(all(t.inputSchema["additionalProperties"] is False for t in tools))
        with patch("pilot_v1.mcp_bridge.build_opener") as opener:
            for name, arguments in [("approve", {}), ('approve_batch', {}), ('get_batch', {'batch_id': 'a'*64, 'execute': True}), ("list_jobs", {"execute": True}),
                                    ("list_jobs", {"limit": "1"}), ("get_source_health", {"url": "http://localhost:3340/api/approve"}),
                                    ("get_finding", {"finding_id": "../api/approve"}),
                                    ("get_job", {"job_id": "a" * 32, "decision": "APPROVE"})]:
                with self.assertRaises(Exception):
                    await server.call_tool(name, arguments)
            opener.assert_not_called()
            with self.assertRaises(ValueError):
                dispatch("/api/jobs/decision", {})
