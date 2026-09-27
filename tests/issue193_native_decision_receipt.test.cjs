const test = require('node:test');
const assert = require('node:assert/strict');
const {recordIfRejectOnly, TOOL} = require('../integration/native-decision-receipt.cjs');
const {patchSource, patchRetainedSource, patchInstalledSource, retainedDigest, retainedPatchedDigest} = require('../integration/patch-librechat-native-decision-receipt.cjs');
const s3SslApprovalHook = require('../integration/s3-ssl-reject-only-approval-hook.cjs');

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
      return {ok: true, json: async () => ({outcome, live_execution_authorized: false, downstream_dispatches: 0, aws_writes: 0,
        ...(decision === 'reject' && {provider_readback: 'UNCHANGED'})})};
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

test('retry after a consumed Reject receipt fails closed without another continuation', async () => {
  let calls = 0;
  const send = async () => {
    calls++;
    if (calls === 1) return {ok: true, json: async () => ({outcome: 'REJECTED',
      live_execution_authorized: false, downstream_dispatches: 0, aws_writes: 0,
      provider_readback: 'UNCHANGED'})};
    return {ok: false, json: async () => ({})};
  };
  const input = {req: request(), job, pendingAction: pending()};
  const first = await recordIfRejectOnly(input, send);
  assert.equal(first.outcome, 'REJECTED');
  await assert.rejects(recordIfRejectOnly(input, send), /durable native decision receipt rejected/);
  assert.equal(calls, 2);
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
  assert.throws(() => patchInstalledSource('unrecognized resume implementation'), /differs from both reviewed/);
});

test('retained runtime patch stays between winning approval validation and provider execution', () => {
  const fixture = [
    'GenerationJobManager.approvals.resolve(',
    '    if (',
    '      !(await GenerationJobManager.beginProviderExecution(',
    'client.resumeCompletion({',
  ].join('\n');
  const patched = patchRetainedSource(fixture);
  assert.equal((patched.match(/recordIfRejectOnly/g) ?? []).length, 1);
  assert.ok(patched.indexOf('recordIfRejectOnly') < patched.indexOf('GenerationJobManager.beginProviderExecution('));
  assert.ok(patched.indexOf('GenerationJobManager.beginProviderExecution(') < patched.indexOf('client.resumeCompletion({'));
  assert.equal(retainedDigest, '54dad95a0e143f5d72857d98c8398743e68e101cab527b38382a7c0d51f10e43');
  assert.equal(retainedPatchedDigest, '9a5ea6723b0daddf7812fba7fb03f47f76183889c3e96a6ad827972f2ad9e0a7');
});

test('s3_ssl native ASK registers exact scope and offers Reject only', async () => {
  const oldFetch = global.fetch;
  let posted;
  process.env.SECOPS_DECISION_RECEIPT_SECRET = 'unit-test-only-key-with-more-than-thirty-two-characters';
  global.fetch = async (_url, options) => {
    posted = JSON.parse(options.body);
    return {ok: true, json: async () => ({registered: true, live_execution_authorized: false})};
  };
  try {
    const hook = s3SslApprovalHook()({userId: 'authenticated-user-123'});
    const result = await hook({toolInput: {control: 's3_ssl', batch_id: args.batch_id, scope_hash: args.scope_hash}});
    assert.deepEqual(posted, {tool: TOOL, control: 's3_ssl', batch_id: args.batch_id,
      scope_hash: args.scope_hash, user_id: 'authenticated-user-123'});
    assert.equal(result.decision, 'ask');
    assert.deepEqual(result.allowedDecisions, ['reject']);
    assert.match(result.reason, /Reject-only validation/);
  } finally {
    global.fetch = oldFetch;
  }
});

test('s3_ssl ASK denies malformed scope before registration', async () => {
  const oldFetch = global.fetch;
  global.fetch = async () => { throw Error('must not reach registration'); };
  try {
    const hook = s3SslApprovalHook()({userId: 'authenticated-user-123'});
    const result = await hook({toolInput: {control: 'restricted-ssh', batch_id: args.batch_id, scope_hash: args.scope_hash}});
    assert.equal(result.decision, 'deny');
  } finally {
    global.fetch = oldFetch;
  }
});
