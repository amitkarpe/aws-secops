# AWS Compliance Agent

A public personal-lab project for **governed agentic AWS SecOps**: an AI operator can read bounded AWS evidence, investigate a supported finding and explain the decision path, while AWS changes remain behind a separate human-approval + policy + exact-tool boundary.

> **Personal lab / POC only. Not a production service.**

## The current story

There are deliberately **two separate planes**.

### 1. Read / investigate — live AgentCore Harness

```text
AWS Config
   ↓
aws_secops_operator Harness — Nova 2 Lite
   ↓ exactly four read tools
AgentCore Gateway + Policy (ENFORCE)
   ↓
Bounded Config / retained-demo S3 reads
   ↓
Evidence + recommendation + Decision Timeline
```

The live Harness can:

- summarize the two supported AWS Config controls;
- list bounded current non-compliant findings;
- investigate one deterministic retained-demo S3 finding when Config returns one;
- show a factual nine-stage Agent Decision Timeline.

It has **no model-accessible AWS write, shell, generic AWS, arbitrary resource-selection or remediation tool**. An explicit `fix/apply/execute` request still does not mutate AWS through the Harness.

### 2. Governed mutation — recorded Demo v1 path

```text
Exact supported remediation intent
   ↓
Human Approve / Reject
   ↓
AgentCore Gateway + Policy
   ↓
Exact S3 or Security Group tool
   ↓
AWS API
   ↓
Direct provider readback
   ↓
AWS Config converges independently
```

The core security principle remains:

> **The AI can investigate and recommend; it does not authorize an AWS change.**

## What is proven

| Capability | Current evidence |
|---|---|
| Read-only Harness | **Live** — exactly four bounded read tools, Gateway Policy `ENFORCE` |
| Config health failure | **Fail closed** — returns `UNVERIFIED/BLOCKED`, not a fabricated result |
| S3 contextual investigation | **Live** — healthy zero-finding path returns Config-only `CLEAR` with provider state `NOT_READ` |
| Agent Decision Timeline | **Live** — nine observable evidence/status stages, never hidden chain-of-thought |
| Explicit fix request through Harness | **No mutation** — remains outside the Harness write boundary |
| Governed S3 + restricted-SSH remediation | **Recorded Demo v1** — human decision, exact tool, provider verification |
| Two-account read-only proof | **Blocked** — no second authorized owned account/read scope is currently connected |

A Config-only `CLEAR` is intentionally narrow: it means no current non-compliant finding was returned by AWS Config. It does **not** mean direct S3 provider state was read, the bucket was proven non-public, or risk was assessed.

## 3-minute demo

Start with the current [Agentic SecOps — 3-minute demo](docs/operations/AGENTIC_DEMO_3_MIN.md).

The short story is:

1. **Finding / status** — read current Config evidence.
2. **Investigation** — use bounded contextual reads only when a current retained-demo finding exists.
3. **Decision Timeline** — show evidence, recommendation and governance state.
4. **Trust test** — ask the Harness to fix it; verify it still has no mutation path.
5. **Proof boundary** — explain that actual remediation uses the separate recorded human-approval → Gateway/Policy → exact-tool → provider-readback path.

This keeps the demo useful even when the current lab is compliant. A live non-compliant S3 investigation can be re-armed only through the explicit operator-only demo path, never through the Harness.

## Recorded Demo v1 scope

| | Recorded scope |
|---|---|
| Resources | **100 S3 buckets + 10 unattached Security Groups** |
| Controls | **S3 Block Public Access + restricted SSH** |
| Approval | **Separate native human decision per action family** |
| Mutation | **Exact tools only; no generic model-accessible AWS write tool** |
| Verification | **Direct provider readback; AWS Config converges independently** |

Demo v1 planners use complete retained-family readiness gates. This is not an arbitrary-subset remediation engine.

## Start here

1. **Short demo:** [Agentic SecOps — 3-minute demo](docs/operations/AGENTIC_DEMO_3_MIN.md)
2. **Management audit view:** [live multi-account acceptance evidence](docs/operations/MANAGEMENT_AUDIT_VIEW.md)
3. **Architecture:** [current two-plane architecture](docs/architecture.md)
4. **Governance:** [why the agent cannot freely change AWS](docs/governance.md)
5. **Long technical demo:** [Demo v1](docs/demo-v1.md)
6. **Current public status:** [PROJECT_STATUS.md](PROJECT_STATUS.md)
7. **Learning portal:** https://amitkarpe.github.io/aws-secops/

### Fresh ChatGPT operator session

Start a new chat with only:

> `Using GitHub app - Read AGENTS.md, CONTEXT.md, active Issue/PR and continue.`

`AGENTS.md` routes ChatGPT to `PROMPT.md`, current context and active GitHub authority. Chat history is not the project source of truth.

## Evidence

Key recorded milestones:

- [PR #23](https://github.com/amitkarpe/aws-secops/pull/23) — governed S3 execution with native approval, Gateway/Policy and provider verification.
- [PR #25](https://github.com/amitkarpe/aws-secops/pull/25) — AWS Config + exact restricted-SSH remediation direction.
- [PR #27](https://github.com/amitkarpe/aws-secops/pull/27) — recorded 100-S3 + 10-SG Demo v1 acceptance.
- [PR #64](https://github.com/amitkarpe/aws-secops/pull/64) — live Harness-native S3 investigation + Decision Timeline.
- [PR #65](https://github.com/amitkarpe/aws-secops/pull/65) — unhealthy Config evidence fails closed as `UNVERIFIED/BLOCKED`.
- [PR #66](https://github.com/amitkarpe/aws-secops/pull/66) — Config-only `CLEAR` cannot be presented as provider verification.

Issue [#60](https://github.com/amitkarpe/aws-secops/issues/60) is the durable authority for the current agentic SecOps phase and live acceptance evidence.

## Important boundaries

- AWS Config, CloudTrail, CloudWatch and direct provider reads remain authoritative AWS evidence sources.
- The Harness is read-only; it does not become a remediation executor when prompted to fix something.
- Human approval, Gateway/Policy, exact tools and IAM remain separate AWS-change controls.
- Provider state, not model confidence, determines remediation completion.
- `UNKNOWN`, `BLOCKED`, `UNVERIFIED` and partial evidence remain explicit.
- No multi-account live claim exists until a second explicitly authorized owned read scope is configured and independently verified.
- No production, arbitrary-resource, generic AWS administration or 1,000-resource claim is made.

## Repository map

```text
docs/implementation/   dated plans and implementation proofs
docs/operations/       current short demo + historical operations material
docs/research/         AgentCore, cost and feasibility research
infra/                  repository-owned AWS infrastructure definitions
integration/           historical/current agent integration code
pilot_v1/              bounded Demo v1 remediation logic
scripts/                deployment, proof and operator helpers
tests/                  deterministic regression tests
```

Historical documents are intentionally retained as engineering evidence. They are not all current architecture authority.

## Contributors / AI workers

Short-session read order:

1. `AGENTS.md` — bootstrap/router and repository rules
2. `CONTEXT.md` — current truth and active authority
3. `PROMPT.md` — full ChatGPT + GitHub + AWS Core operating model
4. active Issue/PR — work authority
5. `SPEC.md` / `ROADMAP.md` when relevant

## Public repository boundary

Treat repository content, Issues/PRs, Actions logs and Git history as public. Do not publish credentials, account IDs, private ARNs/endpoints, authentication data, session IDs, raw private findings or private screenshots.

## Status

**Issue #60 Milestones 1–2 are live-deployed and healthy-path accepted on the read-only AgentCore Harness. Milestone 3 is blocked pending a second explicitly authorized owned AWS read scope. Milestone 4 is consolidating the short demo and public documentation around the verified current architecture.**
