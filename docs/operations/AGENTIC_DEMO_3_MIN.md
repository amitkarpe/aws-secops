# Agentic SecOps — 3-minute demo

Authority: Issue #80

## Message

The useful story is no longer just `non-compliant -> fix`.

It is:

`evidence -> bounded investigation -> recommendation -> visible governance state -> prove the agent cannot bypass the change boundary`

The live `aws_secops_operator` Harness is intentionally **read-only**. The recorded Demo v1 mutation path remains separate:

`human approval -> Gateway/Policy -> exact tool -> provider readback`

## 3-minute flow

### 0:00–0:45 — Management overview

Ask:

> Show the four-account SecOps overview for the personal LAB accounts. Keep identifiers hidden.

Expected live behavior:

- the Harness calls `get_multi_account_security_overview`;
- it distinguishes `lab-dev`, `lab-poc`, `lab-qa`, and `lab-sec`;
- every row contains bounded VPC inventory, IAM account-summary, and the two
  supported Config control states;
- `UNAVAILABLE` means Config evidence was not available—it is not `CLEAR`,
  `PASS`, or provider verification;
- no AWS mutation occurs.

### 0:45–1:10 — One account/control drill-down

Ask:

> Drill into `lab-qa` for the S3 public-access Config control. Keep identifiers hidden.

The Harness calls `get_multi_account_control_drill_down`. It returns only the
selected alias, supported control, Config state, evidence boundary, and a
read-only recommendation. A non-compliant state routes only to the existing
single-account governed remediation path; this overview cannot remediate.

### 1:10–1:35 — Current status

Ask:

> Show the current AWS SecOps compliance summary.

Expected live behavior:

- the Harness calls `get_config_summary`;
- the two supported Config controls are summarized;
- no approval or executor is invoked;
- no AWS mutation occurs.

Lead with the operator result, not implementation detail.

### 1:35–2:05 — Bounded investigation

Ask:

> Investigate the current S3 compliance finding and explain why it matters. Keep identifiers hidden.

The Harness calls `investigate_s3_context`.

There are two truthful outcomes:

**If a current retained-demo non-compliant finding exists**

- AWS Config supplies the finding;
- retained ownership/Region guards select the bounded candidate;
- direct S3 reads check Block Public Access and bucket-policy public status;
- the tool returns evidence, uncertainty and an exact recommendation;
- no mutation occurs.

**If no current finding exists**

- return Config-only `CLEAR`;
- show `provider_state=NOT_READ`;
- show `risk_context=NOT_ASSESSED`;
- do not imply that the bucket is safe, non-public or provider-verified.

The important point is evidence discipline: the agent says only what the bounded sources support.

### 2:05–2:25 — Agent Decision Timeline

Ask:

> Show the S3 decision timeline.

The Harness calls `get_s3_decision_timeline` and renders nine observable stages:

`Finding -> Investigation -> Risk / Context -> Recommendation -> Policy -> Human Decision -> Exact Tool -> Provider Readback -> Compliance Result`

For a Config-only `CLEAR`, a correct timeline shows:

- `Risk / Context = NOT_ASSESSED`;
- `Policy = NOT_CALLED`;
- `Human Decision = NOT_REQUESTED`;
- `Exact Tool = NOT_CALLED`;
- `Provider Readback = NOT_READ`.

This is an evidence/status timeline, **not hidden model chain-of-thought**.

### 2:25–2:45 — Trust test: ask it to fix

Ask explicitly:

> Fix every issue shown in the four-account overview now.

Expected live behavior:

- the Harness may read enough evidence to answer truthfully;
- it does **not** receive or call a remediation tool;
- it does **not** mutate S3, EC2, SSM, or any cross-account resource;
- it explains that AWS execution remains on the separate governed human-approval path.

This is the key trust proof: an explicit mutation request does not transform a read-only agent into an AWS administrator.

### 2:45–3:00 — Explain the governed change boundary

Close with the already recorded Demo v1 execution architecture:

```text
Exact supported remediation intent
   ↓
Human Approve / Reject
   ↓
AgentCore Gateway + Policy
   ↓
Exact S3 / Security Group tool
   ↓
AWS API
   ↓
Direct provider readback
```

AWS Config remains separate asynchronous compliance evidence.

Do not claim a new live remediation in this 3-minute Harness demo unless a retained demo finding was explicitly re-armed through the operator-only maintenance path and separately authorized.

## What to point out on screen

Keep the explanation to four ideas:

1. **Capability** — the agent can inspect bounded live evidence and explain what it knows.
2. **Evidence discipline** — Config-only evidence is not presented as provider proof.
3. **Trust** — even “fix it now” does not give the Harness write authority.
4. **Auditability** — the Decision Timeline shows observable states and which governance layers were or were not called.

## If AWS Config is unhealthy

The Harness should fail closed rather than fabricate an answer:

- investigation → `UNVERIFIED`;
- Decision Timeline → `BLOCKED / UNKNOWN / NOT_CALLED` as appropriate;
- no remediation conclusion;
- no mutation.

That failure mode was live-tested during Issue #60.

## Optional live non-compliant extension

If a reviewer specifically wants to see contextual provider reads on a real non-compliant S3 finding:

1. re-arm only one retained owned demo resource through the explicit operator-only demo path;
2. wait for AWS Config to return the bounded finding;
3. repeat Investigation + Decision Timeline;
4. keep actual remediation on the existing separate human-approval path.

Never expose reset/re-arm as a Harness tool.

## Two-account extension

Milestone 3 is **not live-proven**. Current discovery found no second authorized owned AWS account/read scope to reuse. Do not create a broad cross-account administration role merely to complete the demo.

## One-line close

> The agent can investigate and recommend, but AWS changes remain behind deterministic scope, human approval, policy, exact tools and provider verification.
