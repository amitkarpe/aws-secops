const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

let validateRejectOnlyAction;
let hasExecutorDispatch;
let flattenText;
let publicDigest;
let validateVisibleRejectCard;
test.before(async () => {
  ({validateRejectOnlyAction, hasExecutorDispatch, flattenText, publicDigest,
    validateVisibleRejectCard} =
    await import('./e2e/issue191_s3_ssl_reject.mjs'));
});

const exactAction = () => ({
  status: 'requires_action',
  createdAt: 1790000000000,
  pendingAction: {
    actionId: 'action-12345678',
    payload: {
      type: 'tool_approval',
      review_configs: [{allowed_decisions: ['reject']}],
      action_requests: [{
        name: 'decide_s3_ssl_reject_only_mcp_aws_compliance_planner',
        tool_call_id: 'call-12345678',
        arguments: JSON.stringify({control: 's3_ssl', batch_id: 'a'.repeat(20), scope_hash: 'b'.repeat(24)}),
      }],
    },
  },
});

test('browser gate accepts one exact reject-only frozen s3_ssl action', () => {
  assert.deepEqual(validateRejectOnlyAction(exactAction()), {
    toolCallId: 'call-12345678', batchId: 'a'.repeat(20), scopeHash: 'b'.repeat(24),
  });
});

test('browser gate rejects changed control, malformed scope, extra arguments, or extra tools', () => {
  const changes = [
    (value) => { value.pendingAction.payload.action_requests[0].arguments = JSON.stringify({control: 'restricted-ssh', batch_id: 'a'.repeat(20), scope_hash: 'b'.repeat(24)}); },
    (value) => { value.pendingAction.payload.action_requests[0].arguments = JSON.stringify({control: 's3_ssl', batch_id: 'a'.repeat(20), scope_hash: 'b'.repeat(23)}); },
    (value) => { value.pendingAction.payload.action_requests[0].arguments = JSON.stringify({control: 's3_ssl', batch_id: 'a'.repeat(20), scope_hash: 'b'.repeat(24), extra: 'no'}); },
    (value) => { value.pendingAction.payload.action_requests.push({...value.pendingAction.payload.action_requests[0]}); },
  ];
  for (const change of changes) {
    const value = exactAction();
    change(value);
    assert.throws(() => validateRejectOnlyAction(value));
  }
});

test('browser gate refuses any approval choices beyond Reject', () => {
  const value = exactAction();
  value.pendingAction.payload.review_configs[0].allowed_decisions = ['approve', 'reject'];
  assert.throws(() => validateRejectOnlyAction(value), /Reject-only approval/);
});

test('visible native card must identify the s3_ssl Reject-only validation', () => {
  const card = {cardCount: 1, expectedToolCallId: '11111111-1111-4111-8111-111111111111',
    actualToolCallId: '11111111-1111-4111-8111-111111111111', rejectButtonCount: 1, approveButtonCount: 0,
    text: 'Reject-only validation for one exact S3 TLS finding.'};
  assert.doesNotThrow(() => validateVisibleRejectCard(card));
  assert.throws(() => validateVisibleRejectCard({...card, cardCount: 2}), /exact visible/);
  assert.throws(() => validateVisibleRejectCard({...card, actualToolCallId: 'call-other'}), /exact visible/);
  assert.throws(() => validateVisibleRejectCard({...card, rejectButtonCount: 0}), /exact visible/);
  assert.throws(() => validateVisibleRejectCard({...card, approveButtonCount: 1}), /exact visible/);
  assert.throws(() => validateVisibleRejectCard({...card, text: 'S3 TLS approval card'}), /exact visible/);
  assert.throws(() => validateVisibleRejectCard({...card, text: 'Reject-only validation for S3 BPA'}), /exact visible/);
});

test('chat transcript flattener preserves only rendered visible text', () => {
  assert.equal(flattenText([{text: 'REJECTED'}, 'UNCHANGED']), 'REJECTED UNCHANGED');
});

test('Reject transcript is rejected if any remediation executor call appears', () => {
  assert.equal(hasExecutorDispatch([{content: [{text: 'REJECTED'}]}]), false);
  assert.equal(hasExecutorDispatch([{tool_calls: [{name: 'execute_multi_account_remediation'}]}]), true);
});

test('browser evidence emits only one-way digests for frozen batch and scope', () => {
  const digest = publicDigest('frozen-public-test-value');
  assert.match(digest, /^[a-f0-9]{64}$/);
  assert.notEqual(digest, 'frozen-public-test-value');
});

test('live runner uses only normal LibreChat UI requests, submits Reject, and bounds cleanup', () => {
  const runner = fs.readFileSync(path.join(__dirname, 'e2e', 'issue191_s3_ssl_reject.mjs'), 'utf8');
  assert.match(runner, /getByRole\('button', \{ name: \/\^reject\$\/i \}\)/);
  assert.match(runner, /await reject\.click\(\)/);
  assert.doesNotMatch(runner, /getByRole\('button', \{ name: \/.*approve/i);
  assert.doesNotMatch(runner, /decision\s*:\s*['"]approve/i);
  assert.match(runner, /deleteConversationInUi\(page, id, observations\)/);
  assert.match(runner, /observeAppResponses\(page\)/);
  assert.match(runner, /authorizationHeaderPresent/);
  assert.match(runner, /page\.waitForResponse/);
  assert.match(runner, /\[data-testid="tool-approval"\]/);
  assert.match(runner, /card\.getByRole\('button', \{ name: \/\^reject\$\/i \}\)/);
  assert.match(runner, /waitForAssistantTurn\(page, 240000, \{approval: true\}\)/);
  assert.match(runner, /await selectComplianceAgent\(page\)/);
  assert.match(runner, /innerText\.trim\(\) === 'Compliance Agent v1'/);
  const statusStart = runner.indexOf('startConversation(page, STATUS_PROMPT)');
  const statusCleanup = runner.indexOf('deleteConversationInUi(page, statusConversationId');
  const rejectStart = runner.indexOf('startConversation(page, REJECT_PROMPT)');
  assert.ok(statusStart >= 0 && statusCleanup > statusStart && rejectStart > statusCleanup,
    'cleanup proof must pass before the approval journey starts');
  assert.match(runner, /getByTestId\('send-button'\)/);
  assert.match(runner, /getByTestId\('text-input'\)/);
  assert.match(runner, /send\.evaluate\(\(button\) => button\.click\(\)\)/);
  assert.match(runner, /waitForFunction\(\(\) =>/);
  assert.match(runner, /do not retry/);
  assert.doesNotMatch(runner, /\bfetch\s*\(|document\.cookie|localStorage|sessionStorage|Bearer\s/);
  assert.match(runner, /getByRole\('menuitem', \{name: \/\^delete\$\/i\}\)/);
  assert.match(runner, /getByRole\('button', \{name: \/\^delete\$\/i\}\)/);
});
