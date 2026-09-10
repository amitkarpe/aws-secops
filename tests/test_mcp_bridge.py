"""Protocol-level boundary tests using the pinned optional official SDK."""
import importlib.util
import unittest
from unittest.mock import patch


@unittest.skipUnless(importlib.util.find_spec("mcp"), "install requirements-mcp.txt for MCP boundary tests")
class McpBoundaryTest(unittest.IsolatedAsyncioTestCase):
    async def test_only_six_tools_reject_extra_args_unknown_tools_and_paths(self):
        from pilot_v1.mcp_bridge import server, dispatch, OPERATIONS
        tools = await server.list_tools()
        self.assertEqual({t.name for t in tools}, OPERATIONS)
        self.assertTrue(all(t.inputSchema["additionalProperties"] is False for t in tools))
        with patch("pilot_v1.mcp_bridge.build_opener") as opener:
            for name, arguments in [("approve", {}), ("list_jobs", {"execute": True}),
                                    ("list_jobs", {"limit": "1"}), ("get_source_health", {"url": "http://localhost:3340/api/approve"}),
                                    ("get_finding", {"finding_id": "../api/approve"}),
                                    ("get_job", {"job_id": "a" * 32, "decision": "APPROVE"})]:
                with self.assertRaises(Exception):
                    await server.call_tool(name, arguments)
            opener.assert_not_called()
            with self.assertRaises(ValueError):
                dispatch("/api/jobs/decision", {})
