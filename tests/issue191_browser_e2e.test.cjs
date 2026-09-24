const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

let validateRejectOnlyAction;
let hasExecutorDispatch;
let flattenText;
let publicDigest;
let validateVisibleRejectCard;
let isExactReadOnlyStatusChat;
let isReadOnlyStatusPromptChat;
let isExactArchiveRequest;
let isExactRejectPromptCardChat;
test.before(async () => {
  ({validateRejectOnlyAction, hasExecutorDispatch, flattenText, publicDigest,
    validateVisibleRejectCard, isExactReadOnlyStatusChat, isReadOnlyStatusPromptChat, isExactArchiveRequest,
    isExactRejectPromptCardChat} =
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
  const card = {cardCount: 1, toolCallId: 'call_opaque-provider-id_123', rejectButtonCount: 1, approveButtonCount: 0,
    text: 'Reject-only validation for one exact S3 TLS finding.'};
  assert.doesNotThrow(() => validateVisibleRejectCard(card));
  assert.throws(() => validateVisibleRejectCard({...card, cardCount: 2}), /exact visible/);
  assert.throws(() => validateVisibleRejectCard({...card, toolCallId: 'short'}), /exact visible/);
  assert.throws(() => validateVisibleRejectCard({...card, toolCallId: 'has whitespace'}), /exact visible/);
  assert.throws(() => validateVisibleRejectCard({...card, toolCallId: null}), /exact visible/);
  assert.throws(() => validateVisibleRejectCard({...card, rejectButtonCount: 0}), /exact visible/);
  assert.throws(() => validateVisibleRejectCard({...card, approveButtonCount: 1}), /exact visible/);
  assert.throws(() => validateVisibleRejectCard({...card, text: 'S3 TLS approval card'}), /exact visible/);
  assert.throws(() => validateVisibleRejectCard({...card, text: 'Reject-only validation for S3 BPA'}), /exact visible/);
});

test('chat transcript flattener preserves only rendered visible text', () => {
  assert.equal(flattenText([{text: 'REJECTED'}, 'UNCHANGED']), 'REJECTED UNCHANGED');
});

test('runner resumes only the exact read-only status chat and never an approval chat', () => {
  const messages = [
    'Read-only: show live s3_ssl status for the four registered LAB aliases. Do not prepare, decide, execute, or remediate.',
    's3_ssl status: lab-dev, lab-poc, lab-qa, lab-sec are AVAILABLE.',
  ];
  assert.equal(isExactReadOnlyStatusChat({messages, approvalCardCount: 0}), true);
  assert.equal(isExactReadOnlyStatusChat({messages: [messages[0].replace('show live', 'show\nlive'), messages[1]], approvalCardCount: 0}), true);
  assert.equal(isExactReadOnlyStatusChat({messages: [messages[0], 's3_ssl status unavailable'], approvalCardCount: 0}), false);
  assert.equal(isExactReadOnlyStatusChat({messages, approvalCardCount: 1}), false);
  assert.equal(isExactReadOnlyStatusChat({messages: [messages[0], 'Prepared batch; submit decision'], approvalCardCount: 0}), false);
  assert.equal(isExactReadOnlyStatusChat({messages: [messages[0].replace('Read-only:', 'Fix:'), messages[1]], approvalCardCount: 0}), false);
});

test('runner reuses only an exact in-progress read-only status prompt', () => {
  const prompt = 'Read-only: show live s3_ssl status for the four registered LAB aliases. Do not prepare, decide, execute, or remediate.';
  assert.equal(isReadOnlyStatusPromptChat({messages: [prompt], approvalCardCount: 0}), true);
  assert.equal(isReadOnlyStatusPromptChat({messages: [prompt, 'status'], approvalCardCount: 0}), true);
  assert.equal(isReadOnlyStatusPromptChat({messages: [prompt.replace('Read-only:', 'Fix:')], approvalCardCount: 0}), false);
  assert.equal(isReadOnlyStatusPromptChat({messages: [prompt], approvalCardCount: 1}), false);
});

test('archive proof must bind the exact conversation and archived state', () => {
  const id = '11111111-1111-4111-8111-111111111111';
  assert.equal(isExactArchiveRequest({conversationId:id,body:{arg:{conversationId:id,isArchived:true}}}), true);
  assert.equal(isExactArchiveRequest({conversationId:id,body:{arg:{conversationId:'22222222-2222-4222-8222-222222222222',isArchived:true}}}), false);
  assert.equal(isExactArchiveRequest({conversationId:id,body:{arg:{conversationId:id,isArchived:false}}}), false);
  assert.equal(isExactArchiveRequest({conversationId:'not-a-uuid',body:{arg:{conversationId:id,isArchived:true}}}), false);
});

test('runner resumes only the exact Reject prompt when one native card is pending', () => {
  const prompt = 'Run the current s3_ssl Reject-only validation: use live evidence, select exactly one current finding, prepare and freeze it, then present its native Reject-only card. Do not Approve, execute remediation, or write to AWS.';
  assert.equal(isExactRejectPromptCardChat({messages:[prompt,'pending'],approvalCardCount:1}), true);
  assert.equal(isExactRejectPromptCardChat({messages:[prompt.replace('exactly one','one') ,'pending'],approvalCardCount:1}), false);
  assert.equal(isExactRejectPromptCardChat({messages:[prompt,'pending'],approvalCardCount:0}), false);
  assert.equal(isExactRejectPromptCardChat({messages:[prompt,'pending','extra'],approvalCardCount:1}), false);
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
  assert.match(runner, /await reject\.click\(\{force: true\}\)/);
  assert.doesNotMatch(runner, /getByRole\('button', \{ name: \/.*approve/i);
  assert.doesNotMatch(runner, /decision\s*:\s*['"]approve/i);
  assert.match(runner, /archiveConversationInUi\(page, id, observations\)/);
  assert.match(runner, /observeAppResponses\(page\)/);
  assert.match(runner, /authorizationHeaderPresent/);
  assert.match(runner, /page\.waitForResponse/);
  assert.match(runner, /POST' && item\.route === '\/api\/convos\/archive'/);
  assert.match(runner, /stage=\$\{activeStage\}/);
  assert.match(runner, /\[data-testid="tool-approval"\]/);
  assert.match(runner, /card\.getByRole\('button', \{ name: \/\^reject\$\/i \}\)/);
  assert.match(runner, /waitForAssistantTurn\(page, 240000, \{approval: true\}\)/);
  assert.doesNotMatch(runner, /composerReady|send\.disabled/);
  assert.match(runner, /await selectComplianceAgent\(page\)/);
  assert.match(runner, /current !== 'My Agents' && current !== ''/);
  assert.match(runner, /unexpected model selection; refusing to send the test prompt/);
  assert.match(runner, /current === 'Compliance Agent v1'/);
  const statusStart = runner.indexOf('startConversation(page, STATUS_PROMPT)');
  const statusCleanup = runner.indexOf('archiveConversationInUi(page, statusConversationId');
  const rejectStart = runner.indexOf('startConversation(page, REJECT_PROMPT)');
  assert.ok(statusStart >= 0 && statusCleanup > statusStart && rejectStart > statusCleanup,
    'cleanup proof must pass before the approval journey starts');
  assert.match(runner, /getByTestId\('send-button'\)/);
  assert.match(runner, /getByTestId\('text-input'\)/);
  assert.match(runner, /send\.evaluate\(\(button\) => button\.click\(\)\)/);
  assert.match(runner, /const routeDeadline = Date\.now\(\) \+ 600000/);
  assert.match(runner, /conversationId = conversationIdFromUrl\(page\.url\(\)\)/);
  assert.match(runner, /while \(!conversationId && Date\.now\(\) < routeDeadline\)/);
  assert.match(runner, /do not retry/);
  assert.doesNotMatch(runner, /\bfetch\s*\(|document\.cookie|localStorage|sessionStorage|Bearer\s/);
  assert.match(runner, /getByRole\('menuitem', \{name: \/\^archive\$\/i\}\)/);
  assert.match(runner, /archiveItem\.evaluate\(\(item\) => item\.click\(\)\)/);
  assert.match(runner, /menuButton\.waitFor\(\{state: 'visible', timeout: 5000\}\)/);
  assert.match(runner, /menuButton\.evaluate\(\(button\) => button\.click\(\)\)/);
  assert.match(runner, /getAttribute\('aria-expanded'\) === 'true'/);
  assert.match(runner, /isExactArchiveRequest\(\{conversationId, body: requestBody\}\)/);
  assert.match(runner, /\.then\(\(response\) => \(\{response\}\), \(\) => \(\{failed: true\}\)\)/);
  assert.match(runner, /document\.querySelectorAll\('a\[href\]'\)/);
  assert.match(runner, /new URL\(link\.href\)\.pathname === `\/c\/\$\{id\}`/);
  assert.match(runner, /native \$\{label\} is obstructed; refusing to continue/);
  assert.match(runner, /requireUnobstructedEnabledButton\(reject, 'Reject'\)/);
  assert.match(runner, /requireUnobstructedEnabledButton\(submit, 'Submit'\)/);
  assert.match(runner, /reject\.click\(\{force: true\}\)/);
  assert.match(runner, /if \(!\(await submit\.isEnabled\(\)\)\)/);
  assert.match(runner, /selectionDeadline = Date\.now\(\) \+ 10000/);
  assert.match(runner, /submit\.evaluate\(\(button\) => button\.click\(\)\)/);
  assert.match(runner, /\/api\/convos\/archive/);
  assert.ok(runner.indexOf('currentExactStatusConversation(page)') < runner.lastIndexOf("page.goto(`${ORIGIN}/c/new`"),
    'check the current tab before navigating away from a reusable status-only conversation');
  assert.doesNotMatch(runner, /deleteConversationInUi|method\(\) === 'DELETE'/);
});
