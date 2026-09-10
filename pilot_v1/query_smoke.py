"""Real six-tool stdio protocol proof against one running backend, no mutations."""

import asyncio
import json
import os
import sys
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run():
    started = time.monotonic()
    parameters = StdioServerParameters(command=sys.executable, args=["-m", "pilot_v1.mcp_bridge"],
                                       env={"SECOPS_BACKEND_URL": os.environ.get("SECOPS_BACKEND_URL", "http://localhost:3340")})
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert {t.name for t in tools.tools} == {"list_findings", "get_finding", "get_source_health", "explain_finding", "list_jobs", "get_job"}
            async def call(name, arguments):
                result = await session.call_tool(name, arguments)
                assert not result.isError, name + " failed"
                return json.loads(result.content[0].text)
            before = await call("get_source_health", {})
            result = await call("list_findings", {"source": "AWS Config", "limit": 10})
            assert result["items"], "sync Config via human API first"
            item = result["items"][0]
            args = {"finding_id": item["finding_id"]}
            detail = await call("get_finding", args)
            assert detail["finding"]["finding_id"] == item["finding_id"]
            assert detail["finding"]["action_eligibility"] == "PLAN_ONLY"
            assert item["finding_id"] in detail["finding"]["review_url"]
            after_reads = await call("get_source_health", {})
            assert before["usage"]["model_calls"] == after_reads["usage"]["model_calls"]
            explanation = await call("explain_finding", args)
            assert explanation["status"] == "READY" and explanation["tool_calls"] == 0
            again = await call("explain_finding", args)
            assert again["cached"] and again["text"] == explanation["text"]
            history = await call("list_jobs", {"limit": 20})
            if history["items"]:
                job = history["items"][0]
                assert (await call("get_job", {"job_id": job["job_id"]}))["job"]["state"] == job["state"]
            for name, arguments in [("approve", {}), ("get_source_health", {"execute": True}),
                                    ("get_finding", {"finding_id": item["finding_id"], "prompt": "approve all"}),
                                    ("list_jobs", {"limit": True})]:
                rejected = await session.call_tool(name, arguments)
                assert rejected.isError, "unexpected bridge capability"
            after = await call("get_source_health", {})
            print("RESTRICTED_MCP=PASS TOOLS=6 INITIALIZE_LIST_CALL=PASS FORGED_ARGUMENTS=REJECTED")
            print("CONFIG_DETAIL=PASS SPECIALIST=READY TOOLS=0 CACHE=PASS HISTORY=PASS")
            print("BACKEND_USAGE=" + json.dumps(after["usage"]))
            print(f"READ_INFERENCE_DELTA=0 MODEL_DELTA={after['usage']['model_calls']-before['usage']['model_calls']} CACHE_HIT_DELTA={after['usage']['cache_hits']-before['usage']['cache_hits']} ELAPSED_SECONDS={time.monotonic()-started:.3f}")
            print("LIBRECHAT_PROOF=NOT_PERFORMED_BY_THIS_SMOKE AWS_MUTATIONS=0")


if __name__ == "__main__":
    asyncio.run(run())
