// Native ASK hook for the exact s3_ssl Reject-only decision tool.
// It registers the authenticated user/batch binding before the card is shown.
const {createHmac} = require('node:crypto');

const TOOL = 'decide_s3_ssl_reject_only_mcp_aws_compliance_planner';
const ENDPOINT = 'http://127.0.0.1:4444/api/operator/native-decision-register';

module.exports = () => (context) => async (input) => {
  const args = input?.toolInput ?? {};
  const userId = context?.userId;
  if (typeof userId !== 'string' || !/^[A-Za-z0-9_-]{8,128}$/.test(userId) ||
      Object.keys(args).sort().join(',') !== 'batch_id,control,scope_hash' ||
      args.control !== 's3_ssl' || !/^[a-f0-9]{20}$/.test(args.batch_id) ||
      !/^[a-f0-9]{24}$/.test(args.scope_hash)) {
    return {decision: 'deny', reason: 'DENY — invalid exact Reject-only scope. No dispatch.'};
  }
  const secret = process.env.SECOPS_DECISION_RECEIPT_SECRET;
  if (typeof secret !== 'string' || secret.length < 32) {
    return {decision: 'deny', reason: 'BLOCKED — native decision receipt unavailable. No dispatch.'};
  }
  const body = JSON.stringify({tool: TOOL, control: args.control, batch_id: args.batch_id,
    scope_hash: args.scope_hash, user_id: userId});
  try {
    const response = await fetch(ENDPOINT, {method: 'POST', body,
      headers: {'Content-Type': 'application/json', Origin: 'http://127.0.0.1:4444',
        'X-SecOps-Decision-Signature': createHmac('sha256', secret).update(body).digest('hex')},
      signal: AbortSignal.timeout(5000)});
    const result = response.ok ? await response.json() : null;
    if (!result?.registered || result?.live_execution_authorized !== false) throw Error('registration rejected');
    return {decision: 'ask', allowedDecisions: ['reject'],
      reason: 'Reject-only validation for one exact S3 TLS finding. Choose Reject, then Submit. The native Reject receipt is durable; no remediation dispatch or AWS resource write is possible.'};
  } catch {
    return {decision: 'deny', reason: 'BLOCKED — exact Reject-only receipt registration failed. No dispatch.'};
  }
};
