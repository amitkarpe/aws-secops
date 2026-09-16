# Agentic SecOps — 3-minute demo

Authority: Issue #60

## Message

The demo is no longer just `non-compliant -> fix`.

It shows:

`finding -> bounded investigation -> recommendation -> governed decision -> exact remediation -> provider proof -> audit timeline`

## 3-minute flow

### 0:00–0:30 — Finding

Ask the AWS Compliance Agent to check the supported S3 Block Public Access control.

Show only the result first: current AWS Config evidence and the retained owned scope. Do not start remediation.

### 0:30–1:15 — Investigation

Ask:

> Investigate the current S3 finding and explain why it matters.

The agent uses `investigate_s3_context` to assemble bounded evidence from the existing operator path. The response should show:

- AWS Config control state;
- retained-owned scope intersection;
- direct provider precondition evidence when available;
- the exact recommendation;
- explicit uncertainty.

The demo must say that control non-compliance does **not** by itself prove sensitive data exposure, attacker activity, exploitability, or business impact.

### 1:15–1:45 — Decision Timeline

Ask:

> Show the decision timeline for this finding.

The agent uses `get_s3_decision_timeline` and shows observable stages only:

`Finding -> Investigation -> Risk / Context -> Recommendation -> Policy -> Human Decision -> Exact Tool -> Provider Readback -> Compliance Result`

This is an evidence/status timeline, not hidden model chain-of-thought.

### 1:45–2:30 — Governed fix

Ask explicitly:

> Fix this S3 compliance issue.

Only now may the agent call `prepare_remediation` and emit the exact S3 executor call. LibreChat presents the native Approve/Reject decision.

If approved:

`human approval -> AgentCore Gateway/Policy -> exact S3 tool -> AWS API`

No generic AWS mutation tool is available to the model.

### 2:30–3:00 — Proof

Refresh the Decision Timeline.

The key closing evidence is:

- direct provider readback for the exact batch;
- `UNKNOWN` is never presented as success;
- AWS Config is shown separately because convergence may lag;
- resource/account identifiers remain hidden by default.

## Two-account extension

The repository also contains the bounded two-account read-only proof implementation. It requires exactly two explicitly configured owned lab accounts in `ap-southeast-1` and exposes no write operation.

Do not present that milestone as live-proven until both account scopes are configured and independently verified.

## One-line close

> The agent can investigate and recommend, but an AWS change still requires the existing deterministic policy, human approval, exact tool, and provider verification boundary.
