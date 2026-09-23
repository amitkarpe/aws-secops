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

async function sameOriginStatus(page, conversationId) {
  return page.evaluate(async (id) => {
    const response = await fetch(`/api/agents/chat/status/${encodeURIComponent(id)}`, {
      credentials: 'same-origin', headers: {
        Accept: 'application/json', 'X-LibreChat-Generation-Protocol': '2',
      },
    });
    let body = null;
    try { body = await response.json(); } catch {}
    return { httpStatus: response.status, body };
  }, conversationId);
}

async function sameOriginMessages(page, conversationId) {
  return page.evaluate(async (id) => {
    const response = await fetch(`/api/messages/${encodeURIComponent(id)}`, {
      credentials: 'same-origin', headers: {
        Accept: 'application/json', 'X-LibreChat-Generation-Protocol': '2',
      },
    });
    let body = null;
    try { body = await response.json(); } catch {}
    return { httpStatus: response.status, body };
  }, conversationId);
}

async function sameOriginDelete(page, conversationId) {
  return page.evaluate(async (id) => {
    const response = await fetch('/api/convos', {
      method: 'DELETE', credentials: 'same-origin',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json',
        'X-LibreChat-Generation-Protocol': '2' },
      body: JSON.stringify({ arg: { conversationId: id } }),
    });
    return response.status;
  }, conversationId);
}

async function startConversation(page, prompt) {
  await page.goto(`${ORIGIN}/c/new`, { waitUntil: 'domcontentloaded' });
  const composer = page.locator('textarea:visible').last();
  await composer.waitFor({ state: 'visible', timeout: 15000 });
  await composer.fill(prompt);
  await composer.press('Enter');
  await page.waitForURL((url) => conversationIdFromUrl(url.href) !== null, { timeout: 30000 });
  return conversationIdFromUrl(page.url());
}

async function waitForSettled(page, conversationId, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const response = await sameOriginStatus(page, conversationId);
    if (response.httpStatus === 401 || response.httpStatus === 403) {
      throw new Error('AUTH_REQUIRED: authenticated chat status is unavailable');
    }
    if (response.httpStatus !== 200 || !response.body || typeof response.body !== 'object') {
      throw new Error('chat status endpoint returned an invalid response');
    }
    if (response.body.status === 'requires_action') return response.body;
    if (response.body.active === false) {
      const messages = await sameOriginMessages(page, conversationId);
      if (messages.httpStatus === 200 && hasPersistedAssistantReply(messages.body)) {
        return {...response.body, persistedMessages: messages.body};
      }
    }
    await page.waitForTimeout(1000);
  }
  throw new Error('conversation did not settle before the bounded deadline');
}

function hasPersistedAssistantReply(messages) {
  if (!Array.isArray(messages)) return false;
  return messages.some((message) => message && typeof message === 'object' &&
    message.isCreatedByUser !== true && message.unfinished !== true &&
    flattenText(message.text || message.content).trim().length > 0);
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
  let submitted = false;
  let cleanup = 'NOT_NEEDED';
  try {
    const pages = browser.contexts().flatMap((context) => context.pages());
    page = pages.find((item) => { try { return new URL(item.url()).origin === ORIGIN; } catch { return false; } });
    if (!page) throw new Error('Compliance Agent tab missing');
    await page.bringToFront();
    if (await page.locator('input[type="password"]:visible').count()) {
      throw new Error('AUTH_REQUIRED: sign in normally in this isolated Chrome profile');
    }
    await page.goto(`${ORIGIN}/c/new`, { waitUntil: 'domcontentloaded' });
    if (await page.locator('input[type="password"]:visible').count()) {
      throw new Error('AUTH_REQUIRED: sign in normally in this isolated Chrome profile');
    }
    const isComplianceAgent = await page.getByText('Compliance Agent v1', { exact: false }).count();
    if (!isComplianceAgent) throw new Error('Compliance Agent v1 is not the selected chat agent');

    const statusConversationId = await startConversation(page, STATUS_PROMPT);
    conversations.push(statusConversationId);
    const readStatus = await waitForSettled(page, statusConversationId, 180000);
    if (readStatus.status === 'requires_action' || readStatus.pendingAction) {
      throw new Error('read-only s3_ssl status unexpectedly requested approval');
    }
    if (hasExecutorDispatch(readStatus.persistedMessages)) {
      throw new Error('read-only status invoked a remediation executor');
    }
    const visibleStatus = await page.locator('body').innerText();
    if (!/s3[_ -]?ssl/i.test(visibleStatus) && !/S3 TLS/i.test(visibleStatus)) {
      throw new Error('read-only status did not identify s3_ssl');
    }
    for (const alias of ALIASES) {
      if (!visibleStatus.includes(alias)) throw new Error('read-only status omitted a registered LAB alias');
    }
    if (/UNAVAILABLE/i.test(visibleStatus)) throw new Error('read-only status reports unavailable evidence');

    const decisionConversationId = await startConversation(page, REJECT_PROMPT);
    conversations.push(decisionConversationId);
    const status = await waitForSettled(page, decisionConversationId, 240000);
    if (status.status !== 'requires_action') throw new Error('chat settled before the native Reject-only card appeared');
    const frozen = validateRejectOnlyAction(status);
    const bodyText = await page.locator('body').innerText();
    if (!/s3[_ -]?ssl/i.test(bodyText) && !/S3 TLS/i.test(bodyText)) {
      throw new Error('visible native card does not identify the s3_ssl validation');
    }
    const reject = page.getByRole('button', { name: /^reject$/i });
    if (await reject.count() !== 1) throw new Error('expected one native Reject button');
    await reject.click();
    const submit = page.getByRole('button', { name: /^submit$/i });
    if (await submit.count() !== 1 || !(await submit.isEnabled())) {
      throw new Error('native Reject selection did not enable one Submit action');
    }
    const resumeResponsePromise = page.waitForResponse((response) => {
      const request = response.request();
      return new URL(response.url()).pathname === '/api/agents/chat/resume' && request.method() === 'POST';
    }, {timeout: 30000});
    await submit.click();
    submitted = true;
    const resumeResponse = await resumeResponsePromise;
    if (![200, 201].includes(resumeResponse.status())) {
      throw new Error(`native Reject resume returned HTTP ${resumeResponse.status()}; do not retry`);
    }

    const completionDeadline = Date.now() + 240000;
    let terminalMessages = null;
    while (Date.now() < completionDeadline) {
      const response = await sameOriginStatus(page, decisionConversationId);
      if (response.httpStatus === 200 && response.body?.active === false &&
          response.body?.status !== 'requires_action') {
        const messages = await sameOriginMessages(page, decisionConversationId);
        if (messages.httpStatus === 200 && hasPersistedAssistantReply(messages.body)) {
          terminalMessages = messages.body;
          break;
        }
      }
      await page.waitForTimeout(1000);
    }
    if (!terminalMessages) throw new Error('Reject was submitted once; persisted conversation did not settle (do not retry)');
    const finalText = flattenText(terminalMessages);
    if (/AWS change applied/i.test(finalText)) throw new Error('Reject path claimed an AWS change');
    if (hasExecutorDispatch(terminalMessages)) throw new Error('Reject path attempted a remediation executor dispatch');
    cleanup = 'PASS';
    for (const id of [...conversations].reverse()) {
      const response = await sameOriginDelete(page, id);
      if (![200, 202, 204].includes(response)) cleanup = 'FAIL';
    }
    conversations.length = 0;
    if (cleanup !== 'PASS') throw new Error('temporary conversation cleanup failed');
    console.log(JSON.stringify({ result: 'PASS', control: 's3_ssl', decision: 'REJECTED',
      frozen_scope_valid: true, native_reject_submitted_once: true, approve_clicked: false,
      batch_digest: publicDigest(frozen.batchId), scope_digest: publicDigest(frozen.scopeHash),
      native_resume_http: resumeResponse.status(), conversation_settled: true,
      executor_dispatch_detected: false, provider_readback: 'verified by durable native-receipt gate',
      conversation_cleanup: cleanup }));
  } finally {
    if (page && !submitted) {
      try {
        for (const id of [...conversations].reverse()) {
          const response = await sameOriginDelete(page, id);
          if (![200, 202, 204].includes(response)) cleanup = 'FAIL';
        }
      } catch { cleanup = 'UNAVAILABLE'; }
    }
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

export {hasExecutorDispatch, hasPersistedAssistantReply, flattenText, publicDigest};
