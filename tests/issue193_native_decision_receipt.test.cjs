const test = require('node:test');
const assert = require('node:assert/strict');
const {recordIfRejectOnly, TOOL} = require('../integration/native-decision-receipt.cjs');
const {patchSource} = require('../integration/patch-librechat-native-decision-receipt.cjs');

process.env.SECOPS_DECISION_RECEIPT_SECRET = 'unit-test-only-key-with-more-than-thirty-two-characters';
const args = {control: 's3_ssl', batch_id: 'a'.repeat(20), scope_hash: 'b'.repeat(24)};
function pending(name = TOOL) {
  return {actionId: 'action-12345678', payload: {action_requests: [
    {name, tool_call_id: 'call-12345678', arguments: JSON.stringify(args)},
  ]}};
}
function request(decision = 'reject') {
  return {user: {id: 'native-user-123'}, body: {decisions: [
    {tool_call_id: 'call-12345678', decision},
  ]}};
}
const job = {createdAt: 1790000000000, metadata: {userId: 'native-user-123'}};

test('legacy BPA and SSH approvals bypass the callback unchanged', async () => {
  let called = 0;
  const send = async () => { called++; throw Error('unexpected receipt call'); };
  for (const name of [
    'execute_multi_account_remediation_mcp_aws_compliance_planner',
    'start_sg_batch_execution_mcp_aws_compliance',
  ]) {
    assert.equal(await recordIfRejectOnly({req: request(), job, pendingAction: pending(name)}, send), null);
  }
  assert.equal(called, 0);
});

for (const [decision, outcome] of [['reject', 'REJECTED'], ['approve', 'APPROVE_BLOCKED']]) {
  test(`${decision} persists before a non-executing continuation`, async () => {
    let calls = 0;
    const send = async (_url, options) => {
      calls++;
      assert.equal(options.method, 'POST');
      assert.equal(options.headers.Origin, 'http://127.0.0.1:4444');
      assert.match(options.headers['X-SecOps-Decision-Signature'], /^[a-f0-9]{64}$/);
      const receipt = JSON.parse(options.body);
      assert.equal(receipt.decision, decision);
      assert.equal(receipt.batch_id, args.batch_id);
      return {ok: true, json: async () => ({outcome, live_execution_authorized: false, downstream_dispatches: 0, aws_writes: 0})};
    };
    const result = await recordIfRejectOnly({req: request(decision), job, pendingAction: pending()}, send);
    assert.equal(calls, 1);
    assert.equal(result.outcome, outcome);
    assert.deepEqual(result.resumeValue, {'call-12345678': {
      type: 'reject', reason: decision === 'approve' ? 'LIVE_EXECUTION_NOT_AUTHORIZED' : 'REJECTED',
    }});
  });
}

test('receipt failure prevents a continuation result', async () => {
  await assert.rejects(recordIfRejectOnly(
    {req: request(), job, pendingAction: pending()},
    async () => { throw Error('receipt backend unavailable'); },
  ), /receipt backend unavailable/);
});

test('unsafe backend response is refused', async () => {
  await assert.rejects(recordIfRejectOnly(
    {req: request('approve'), job, pendingAction: pending()},
    async () => ({ok: true, json: async () => ({outcome: 'APPROVE', live_execution_authorized: true, downstream_dispatches: 1, aws_writes: 1})}),
  ), /unsafe outcome/);
});

test('wrong control, scope, tool count, user, and decision fail before sending', async () => {
  const send = async () => { throw Error('unexpected receipt call'); };
  const changes = [
    {req: request(), job, pendingAction: {...pending(), payload: {action_requests: [{...pending().payload.action_requests[0], arguments: JSON.stringify({...args, control: 'restricted-ssh'})}]}}},
    {req: request(), job, pendingAction: {...pending(), payload: {action_requests: [{...pending().payload.action_requests[0], arguments: JSON.stringify({...args, scope_hash: 'c'.repeat(23)})}]}}},
    {req: request(), job, pendingAction: {...pending(), payload: {action_requests: [...pending().payload.action_requests, pending().payload.action_requests[0]]}}},
    {req: {...request(), user: {id: 'wrong-user-123'}}, job, pendingAction: pending()},
    {req: request('edit'), job, pendingAction: pending()},
  ];
  for (const input of changes) await assert.rejects(recordIfRejectOnly(input, send));
});

test('resume patch refuses source drift', () => {
  assert.throws(() => patchSource('unrecognized resume implementation'), /differs from pinned/);
});
