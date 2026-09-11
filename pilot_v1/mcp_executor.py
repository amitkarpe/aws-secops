"""Separate one-tool MCP entry. Deploy with native LibreChat ASK, never allow."""
import json
from urllib.request import Request, build_opener, ProxyHandler
from mcp.server.fastmcp import FastMCP
from pydantic import ConfigDict
from .mcp_bridge import backend_url, NoRedirect
from .queries import identity

server = FastMCP('AWS SecOps exact batch execution', instructions='One exact frozen batch only. Native human ASK approval is required. No session-wide approval, arbitrary resource or generic AWS action.')


@server.tool()
def start_batch_execution(batch_id: str, approval_hash: str) -> dict:
    """ASK: Approve & Execute this exact frozen S3 batch once. Reject = no dispatch.

    Enables all four bucket Block Public Access settings only on resources in
    the current immutable preview. Gateway Policy must independently allow each
    action. Returns durable progress quickly; get_batch reads verified results.
    Neither chat text nor an edited resource list can authorize a different scope.
    """
    identity(batch_id); identity(approval_hash)
    base = backend_url('get_batch')
    request = Request(base+'/api/bulk/start', data=json.dumps(dict(batch_id=batch_id, approval_hash=approval_hash)).encode(),
                      headers={'Content-Type': 'application/json', 'Origin': base})
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=30) as response:
            raw = response.read(16001)
        if len(raw) > 16000:
            raise ValueError('oversized execution result')
        value = json.loads(raw)
        if value.get('version') != 1 or value.get('batch_id') != batch_id:
            raise ValueError('unexpected execution result')
        return value
    except Exception:
        raise ValueError('Start unavailable or rejected. Outcome may be unknown: read get_batch; do not blindly retry or claim success.') from None


for tool in server._tool_manager.list_tools():
    model = tool.fn_metadata.arg_model
    model.model_config = ConfigDict(extra='forbid', strict=True)
    model.model_rebuild(force=True)
    tool.parameters = model.model_json_schema()

if __name__ == '__main__':
    backend_url('get_batch')
    server.run(transport='stdio')
