// LibreChat v0.8.8-rc1 resume seam. No AWS or executor dependency.
const {createHmac} = require('node:crypto');

const TOOL = 'decide_s3_ssl_reject_only_mcp_aws_compliance_planner';
const ENDPOINT = 'http://127.0.0.1:4444/api/operator/native-decision-receipt';

async function recordIfRejectOnly({req, job, pendingAction}, send = fetch) {
  const actions = pendingAction?.payload?.action_requests;
  if (!Array.isArray(actions) || !actions.some((action) => action?.name === TOOL)) return null;
  if (actions.length !== 1 || actions[0]?.name !== TOOL) throw Error('reject-only action must be single and exact');
  const action = actions[0];
  const resolutions = req?.body?.decisions;
  if (!Array.isArray(resolutions) || resolutions.length !== 1 ||
      resolutions[0]?.tool_call_id !== action.tool_call_id ||
      !['reject', 'approve'].includes(resolutions[0]?.decision)) {
    throw Error('reject-only native decision mismatch');
  }
  let args = action.arguments;
  if (typeof args === 'string') args = JSON.parse(args);
  if (!args || typeof args !== 'object' || Array.isArray(args) ||
      Object.keys(args).sort().join(',') !== 'batch_id,control,scope_hash' ||
      args.control !== 's3_ssl' || !/^[a-f0-9]{20}$/.test(args.batch_id) ||
      !/^[a-f0-9]{24}$/.test(args.scope_hash)) {
    throw Error('reject-only frozen scope mismatch');
  }
  const secret = process.env.SECOPS_DECISION_RECEIPT_SECRET;
  if (typeof secret !== 'string' || secret.length < 32) throw Error('decision receipt key unavailable');
  const userId = req?.user?.id;
  if (typeof userId !== 'string' || !userId || job?.metadata?.userId !== userId ||
      typeof pendingAction.actionId !== 'string' || !Number.isSafeInteger(job.createdAt)) {
    throw Error('authenticated native binding unavailable');
  }
  const receipt = {
    tool: TOOL, control: 's3_ssl', batch_id: args.batch_id, scope_hash: args.scope_hash,
    action_id: pendingAction.actionId, generation_id: String(job.createdAt),
    user_id: userId, decision: resolutions[0].decision,
    decided_at: Math.floor(Date.now() / 1000),
  };
  const body = JSON.stringify(receipt);
  const signature = createHmac('sha256', secret).update(body).digest('hex');
  const response = await send(ENDPOINT, {
    method: 'POST', headers: {
      'Content-Type': 'application/json', Origin: 'http://127.0.0.1:4444',
      'X-SecOps-Decision-Signature': signature,
    },
    body, signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw Error('durable native decision receipt rejected');
  const result = await response.json();
  const expected = receipt.decision === 'reject' ? 'REJECTED' : 'APPROVE_BLOCKED';
  if (result?.outcome !== expected || result?.live_execution_authorized !== false ||
      result?.downstream_dispatches !== 0 || result?.aws_writes !== 0) {
    throw Error('native decision receipt returned unsafe outcome');
  }
  // Native Reject skips the tool. Map blocked Approve to that same SDK result,
  // so no MCP/CodeBuild/Gateway/Lambda execution can follow this decision.
  return {resumeValue: {
    [action.tool_call_id]: {
      type: 'reject',
      reason: receipt.decision === 'approve'
        ? 'LIVE_EXECUTION_NOT_AUTHORIZED' : 'REJECTED',
    },
  }, outcome: expected};
}

module.exports = {recordIfRejectOnly, TOOL};
