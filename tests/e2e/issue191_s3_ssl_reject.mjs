#!/usr/bin/env node
/* Authenticated LibreChat UI proof for Issue #191. Uses an existing isolated
 * Chrome profile through local CDP; never reads/export auth or browser state. */
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';

const TOOL = 'decide_s3_ssl_reject_only_mcp_aws_compliance_planner';
const ORIGIN = 'https://sec.astromedicomp.org';
const STATUS_PROMPT = 'Read-only: show live s3_ssl status for the four registered LAB aliases. Do not prepare, decide, execute, or remediate.';
const REJECT_PROMPT = 'Run the current s3_ssl Reject-only validation: use live evidence, select exactly one current finding, prepare and freeze it, then present its native Reject-only card. Do not Approve, execute remediation, or write to AWS.';
const ALIASES = ['lab-dev', 'lab-poc', 'lab-qa', 'lab-sec'];
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function validateRejectOnlyAction(status) {
  const pending = status?.pendingAction;
  const payload = pending?.payload;
  const requests = payload?.action_requests;
  if (status?.status !== 'requires_action' || payload?.type !== 'tool_approval' ||
      !Array.isArray(requests) || requests.length !== 1 || !Array.isArray(payload.review_configs) ||
      payload.review_configs.length !== 1 ||
      JSON.stringify(payload.review_configs[0]?.allowed_decisions) !== JSON.stringify(['reject'])) {
    throw new Error('native action is not one exact Reject-only approval');
  }
  const action = requests[0];
  let args = action?.arguments;
  if (typeof args === 'string') args = JSON.parse(args);
  if (action?.name !== TOOL || !args || Array.isArray(args) ||
      Object.keys(args).sort().join(',') !== 'batch_id,control,scope_hash' ||
      args.control !== 's3_ssl' || !/^[a-f0-9]{20}$/.test(args.batch_id) ||
      !/^[a-f0-9]{24}$/.test(args.scope_hash) ||
      typeof action.tool_call_id !== 'string' || action.tool_call_id.length < 8 ||
      typeof pending.actionId !== 'string' || pending.actionId.length < 8 ||
      !Number.isSafeInteger(status.createdAt)) {
    throw new Error('native action is not bound to the exact frozen s3_ssl scope');
  }
  return { toolCallId: action.tool_call_id, batchId: args.batch_id, scopeHash: args.scope_hash };
}

export function validateVisibleRejectCard({cardCount, expectedToolCallId, actualToolCallId, rejectButtonCount, approveButtonCount, text}) {
  if (cardCount !== 1 || typeof expectedToolCallId !== 'string' ||
      !UUID.test(expectedToolCallId) || actualToolCallId !== expectedToolCallId ||
      rejectButtonCount !== 1 || approveButtonCount !== 0 || typeof text !== 'string' ||
      (!/s3[_ -]?ssl/i.test(text) && !/S3 TLS/i.test(text)) ||
      !/Reject-only validation/i.test(text)) {
    throw new Error('native card is not the exact visible s3_ssl Reject-only action');
  }
}

function observeAppResponses(page) {
  const observations = [];
  page.on('response', (response) => {
    let url;
    try { url = new URL(response.url()); } catch { return; }
    if (url.origin !== ORIGIN || !/^\/api\/(?:convos|messages|agents\/chat\/status|agents\/chat\/resume)(?:\/|$)/.test(url.pathname)) return;
    const request = response.request();
    const headers = request.headers();
    observations.push({method: request.method(), route: url.pathname.replace(/[0-9a-f-]{24,}/gi, ':id'),
      status: response.status(),
      authorizationHeaderPresent: Object.keys(headers).some((name) => name.toLowerCase() === 'authorization')});
  });
  return observations;
}

async function waitForAssistantTurn(page, timeoutMs, {approval = false} = {}) {
  const deadline = Date.now() + timeoutMs;
  const card = page.locator('[data-testid="tool-approval"]');
  while (Date.now() < deadline) {
    if (approval && await card.count() === 1 && await card.isVisible()) return {approval: true};
    const turn = await page.evaluate(() => {
      const bodies = [...document.querySelectorAll('[data-testid="message-body"]')];
      const send = document.querySelector('[data-testid="send-button"]');
      const text = bodies.at(-1)?.innerText?.trim() ?? '';
      const stopVisible = [...document.querySelectorAll('button')].some((button) =>
        /stop generating/i.test(button.getAttribute('aria-label') ?? ''));
      return {bodyCount: bodies.length, assistantText: text,
        composerReady: Boolean(send && !send.disabled), stopVisible};
    });
    if (turn.bodyCount >= 2 && turn.assistantText && turn.composerReady && !turn.stopVisible) {
      return {approval: false, assistantText: turn.assistantText};
    }
    await page.waitForTimeout(500);
  }
  throw new Error(approval ? 'native Reject-only approval card did not appear before the bounded deadline' :
    'LibreChat did not render a settled assistant turn before the bounded deadline');
}

async function deleteConversationInUi(page, conversationId, observations) {
  const observationStart = observations.length;
  const menuButton = page.locator(`button[id="conversation-menu-${conversationId}"]`);
  await menuButton.waitFor({state: 'attached', timeout: 15000});
  await menuButton.waitFor({state: 'visible', timeout: 5000});
  await clickUiControl(page, menuButton);
  const deleteItem = page.getByRole('menuitem', {name: /^delete$/i});
  await deleteItem.waitFor({state: 'visible', timeout: 5000});
  await clickUiControl(page, deleteItem);
  const dialog = page.getByRole('dialog');
  await dialog.waitFor({state: 'visible', timeout: 5000});
  const confirmation = dialog.getByRole('button', {name: /^delete$/i});
  if (await confirmation.count() !== 1 || !(await confirmation.isEnabled())) {
    throw new Error('native conversation cleanup confirmation is not uniquely available');
  }
  const deletionResponse = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return url.origin === ORIGIN && url.pathname === '/api/convos' && response.request().method() === 'DELETE';
  }, {timeout: 20000});
  await clickUiControl(page, confirmation);
  const response = await deletionResponse;
  if (![200, 201, 202, 204].includes(response.status())) {
    throw new Error(`native cleanup returned HTTP ${response.status()}`);
  }
  await page.waitForFunction((id) => !document.querySelector(`button[id="conversation-menu-${id}"]`), conversationId,
    {timeout: 15000});
  const deletion = observations.slice(observationStart).find((item) => item.method === 'DELETE' && /\/api\/convos(?:\/|$)/.test(item.route));
  if (!deletion || ![200, 201, 202, 204].includes(deletion.status) || !deletion.authorizationHeaderPresent) {
    throw new Error('native cleanup did not complete through the authenticated LibreChat client');
  }
  return deletion.status;
}

async function clickUiControl(page, locator) {
  const bounds = await locator.boundingBox();
  if (!bounds) throw new Error('native UI control has no visible bounds');
  await page.mouse.click(bounds.x + bounds.width / 2, bounds.y + bounds.height / 2);
}

async function selectComplianceAgent(page) {
  const selector = page.getByTestId('model-selector-button');
  await selector.waitFor({state: 'visible', timeout: 15000});
  if ((await selector.innerText()).trim() === 'Compliance Agent v1') return;
  await page.waitForFunction(() =>
    document.querySelector('[data-testid="model-selector-button"]')?.innerText.trim() === 'Compliance Agent v1',
  null, {timeout: 20000}).catch(() => {
    throw new Error('Compliance Agent v1 is not selected for this chat');
  });
  if ((await selector.innerText()).trim() !== 'Compliance Agent v1') {
    throw new Error('Compliance Agent v1 is not selected for this chat');
  }
}

async function startConversation(page, prompt) {
  if (new URL(page.url()).pathname !== '/c/new') {
    await page.goto(`${ORIGIN}/c/new`, { waitUntil: 'domcontentloaded' });
  }
  if (await page.locator('input[type="password"]:visible').count()) {
    throw new Error('AUTH_REQUIRED: sign in normally in this isolated Chrome profile');
  }
  await selectComplianceAgent(page);
  const composer = page.getByTestId('text-input');
  if (await composer.count() !== 1) throw new Error('expected one native LibreChat message input');
  await composer.waitFor({ state: 'visible', timeout: 15000 });
  await composer.fill(prompt);
  const send = page.getByTestId('send-button');
  if (await send.count() !== 1 || !(await send.isEnabled())) {
    throw new Error('chat composer did not expose one enabled Send action');
  }
  await send.evaluate((button) => button.click());
  await page.waitForFunction(() =>
    /^\/c\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(location.pathname),
  null, {timeout: 30000});
  return conversationIdFromUrl(page.url());
}

function flattenText(value) {
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return value.map(flattenText).join(' ');
  if (value && typeof value === 'object') return Object.values(value).map(flattenText).join(' ');
  return '';
}

function hasExecutorDispatch(messages) {
  const visit = (value) => {
    if (Array.isArray(value)) return value.some(visit);
    if (!value || typeof value !== 'object') return false;
    if (typeof value.name === 'string' && value.name.startsWith('execute_multi_account_remediation')) return true;
    return Object.values(value).some(visit);
  };
  return visit(messages);
}

function publicDigest(value) {
  return createHash('sha256').update(value).digest('hex');
}

function conversationIdFromUrl(url) {
  const match = new URL(url).pathname.match(/^\/c\/([^/]+)$/);
  return match && UUID.test(match[1]) ? match[1] : null;
}

async function run() {
  const [, , cdpUrl, corePath] = process.argv;
  if (!cdpUrl || !corePath) throw new Error('usage: issue191_s3_ssl_reject.mjs <localhost-cdp-url> <playwright-core-index.mjs>');
  const { chromium } = await import(pathToFileURL(corePath).href);
  const browser = await chromium.connectOverCDP(cdpUrl, { noDefaults: true, timeout: 30000 });
  let page;
  const conversations = [];
  let cleanup = 'NOT_NEEDED';
  let observations = [];
  try {
    const pages = browser.contexts().flatMap((context) => context.pages());
    page = pages.find((item) => { try { return new URL(item.url()).origin === ORIGIN; } catch { return false; } });
    if (!page) throw new Error('Compliance Agent tab missing');
    await page.bringToFront();
    observations = observeAppResponses(page);
    if (await page.locator('input[type="password"]:visible').count()) {
      throw new Error('AUTH_REQUIRED: sign in normally in this isolated Chrome profile');
    }
    if (new URL(page.url()).pathname !== '/c/new') {
      await page.goto(`${ORIGIN}/c/new`, { waitUntil: 'domcontentloaded' });
    }
    if (await page.locator('input[type="password"]:visible').count()) {
      throw new Error('AUTH_REQUIRED: sign in normally in this isolated Chrome profile');
    }
    const statusConversationId = await startConversation(page, STATUS_PROMPT);
    conversations.push(statusConversationId);
    const readStatus = await waitForAssistantTurn(page, 180000);
    if (/approve|submit decision|prepared batch/i.test(readStatus.assistantText)) {
      throw new Error('read-only s3_ssl status unexpectedly asked for a decision');
    }
    const visibleStatus = await page.locator('body').innerText();
    if (!/s3[_ -]?ssl/i.test(visibleStatus) && !/S3 TLS/i.test(visibleStatus)) {
      throw new Error('read-only status did not identify s3_ssl');
    }
    for (const alias of ALIASES) {
      if (!visibleStatus.includes(alias)) throw new Error('read-only status omitted a registered LAB alias');
    }
    if (/UNAVAILABLE/i.test(visibleStatus)) throw new Error('read-only status reports unavailable evidence');
    await page.reload({waitUntil: 'domcontentloaded'});
    await page.getByTestId('message-body').first().waitFor({state: 'visible', timeout: 15000});
    const historyRead = [...observations].reverse().find((item) => item.method === 'GET' &&
      /\/api\/messages(?:\/|$)/.test(item.route) && item.status >= 200 && item.status < 400 && item.authorizationHeaderPresent);
    if (!historyRead) throw new Error('authenticated UI history reload did not produce a successful LibreChat client read');

    await deleteConversationInUi(page, statusConversationId, observations);
    conversations.splice(conversations.indexOf(statusConversationId), 1);
    const decisionConversationId = await startConversation(page, REJECT_PROMPT);
    conversations.push(decisionConversationId);
    await waitForAssistantTurn(page, 240000, {approval: true});
    const card = page.locator('[data-testid="tool-approval"]');
    const cardCount = await card.count();
    const toolCallId = cardCount === 1 ? await card.getAttribute('data-tool-call-id') : null;
    const rejectButtonCount = cardCount === 1 ? await card.getByRole('button', {name: /^reject$/i}).count() : 0;
    const approveButtonCount = cardCount === 1 ? await card.getByRole('button', {name: /^approve$/i}).count() : 0;
    validateVisibleRejectCard({cardCount, expectedToolCallId: toolCallId,
      actualToolCallId: toolCallId,
      rejectButtonCount, approveButtonCount,
      text: cardCount === 1 ? await card.innerText() : ''});
    const reject = card.getByRole('button', { name: /^reject$/i });
    if (await reject.count() !== 1) throw new Error('expected one native Reject button');
    await reject.click();
    const submit = card.getByRole('button', { name: /^submit$/i });
    if (await submit.count() !== 1 || !(await submit.isEnabled())) {
      throw new Error('native Reject selection did not enable one Submit action');
    }
    const resumeResponsePromise = page.waitForResponse((response) => {
      const request = response.request();
      return new URL(response.url()).pathname === '/api/agents/chat/resume' && request.method() === 'POST';
    }, {timeout: 30000});
    await submit.click();
    const resumeResponse = await resumeResponsePromise;
    if (![200, 201].includes(resumeResponse.status())) {
      throw new Error(`native Reject resume returned HTTP ${resumeResponse.status()}; do not retry`);
    }

    await card.waitFor({state: 'detached', timeout: 240000});
    const settled = await waitForAssistantTurn(page, 30000);
    const finalText = settled.assistantText;
    if (/AWS change applied/i.test(finalText)) throw new Error('Reject path claimed an AWS change');
    if (!/reject(ed|ion)/i.test(finalText)) throw new Error('Reject completion did not render its final decision result');
    cleanup = 'PASS';
    for (const id of [...conversations].reverse()) {
      await deleteConversationInUi(page, id, observations);
    }
    conversations.length = 0;
    if (cleanup !== 'PASS') throw new Error('temporary conversation cleanup failed');
    console.log(JSON.stringify({ result: 'PASS', control: 's3_ssl', decision: 'REJECTED',
      server_scope_authority: 'durable receipt gate', native_reject_submitted_once: true, approve_clicked: false,
      native_tool_call_digest: publicDigest(toolCallId),
      native_resume_http: resumeResponse.status(), conversation_settled: true,
      conversation_cleanup: cleanup,
      authenticated_client_responses: observations.filter((item) => item.authorizationHeaderPresent && item.status >= 200 && item.status < 400).length,
      authenticated_history_read: true }));
  } finally {
    await browser.close();
  }
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
  run().catch((error) => {
    const message = String(error?.message ?? 'unknown failure').replace(/[\r\n]+/g, ' ').slice(0, 240);
    console.error(`ISSUE191_UI_E2E=FAIL ${message}`);
    process.exitCode = 1;
  });
}

export {hasExecutorDispatch, flattenText, publicDigest};
