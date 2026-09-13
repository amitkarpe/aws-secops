# AWS Compliance Agent

A public personal-lab project for **governed AWS compliance remediation**: AWS Config detects, an AI agent explains and plans, a human approves, AgentCore Gateway + Policy govern an exact tool, and direct AWS provider readback verifies the result.

> **Demo v1 is a learning/POC environment, not a production service.**

## Demo v1 at a glance

| | Recorded Demo v1 scope |
|---|---|
| Resources | **100 S3 buckets + 10 unattached Security Groups** |
| Controls | **S3 Block Public Access + restricted SSH** |
| Approval | **Separate native human decision per action family** |
| Mutation | **Exact tools only; no generic model-accessible AWS write tool** |
| Verification | **Direct provider readback; AWS Config converges independently** |

```text
AWS Config
   ↓ Detect
AWS Compliance Agent
   ↓ Explain + plan
Human Approve / Reject
   ↓ Authorize exact intent
AgentCore Gateway + Policy
   ↓ Govern
Exact S3 / Security Group tool
   ↓ Execute
AWS provider readback
   ↓ Verify
AWS Config convergence
```

The core security principle is simple:

> **The AI recommends the change; it does not authorize the change.**

## What the AI actually does

The model helps an operator understand findings, summarize current evidence and map an explicit request onto one of the supported workflows. Deterministic server code owns the supported controls, retained manifests, eligibility rules, exact action, durable batch state and provider verification.

For the recorded S3 bulk workflow, the model is **not** deciding bucket-by-bucket changes. The exact batch worker performs the bounded execution.

This project therefore demonstrates an interactive governed workflow; it does not claim that AI replaces AWS Config remediation or deterministic automation.

## Start here

1. **Learning portal:** https://amitkarpe.github.io/aws-secops/
2. Read [Architecture](docs/architecture.md) for the current control path.
3. Read [Demo v1](docs/demo-v1.md) for the current end-to-end flow, evidence and safe prompts.
4. Read [Governance](docs/governance.md) for trust assumptions, approval, Policy, exact-tool and verification boundaries.
5. Read [Learning path](docs/learning-path.md) for deeper proofs, operations material and clearly labelled history.
6. Read [Project status](PROJECT_STATUS.md) for the current public baseline and known limits.

## What this project is — and is not

This project focuses on the gap **after detection**. It does not try to replace AWS Config, CloudTrail, CloudWatch, CloudSCAPE or VAPT tooling.

The agent is intentionally bounded:

- read-only questions are intended to remain read-only and were tested that way in the recorded demo;
- only supported, server-owned remediation families can be prepared;
- the current planners require the **complete retained family** to pass readiness/eligibility gates; Demo v1 is not an arbitrary-subset remediation engine;
- the model cannot choose arbitrary account, Region, API, resource IDs or AWS action at execution time;
- S3 and Security Group approvals remain independent;
- provider state, not model confidence, determines completion;
- `UNKNOWN`, `FAILED` and partial outcomes remain explicit;
- Demo v1 does not claim multi-account, hostile multi-tenant or production-ready identity governance.

## Evidence

The public site links the detailed proofs. The current story is anchored by these milestones:

- [PR #23](https://github.com/amitkarpe/aws-secops/pull/23) — governed S3 execution with native approval, Gateway/Policy and provider verification.
- [PR #25](https://github.com/amitkarpe/aws-secops/pull/25) — AWS Config + exact restricted-SSH remediation and the unified compliance-agent direction.
- [PR #27](https://github.com/amitkarpe/aws-secops/pull/27) — current Config-driven planner, separate S3/SG approvals, repeatable Operator flow and final Demo v1 acceptance.

See [Demo v1 — evidence digest](docs/demo-v1.md#current-evidence-digest) for what is recorded as proven versus what remains a limitation.

## Repository map

```text
docs/implementation/   dated plans and implementation proofs
docs/operations/       current + historical runbooks/demo material
docs/research/         AgentCore, cost and feasibility research
integration/           LibreChat / MCP / agent integration
pilot_v1/              bounded application and remediation logic
scripts/               deployment, proof and operator helpers
tests/                 deterministic regression tests
```

Historical documents are intentionally retained as engineering evidence. They are not all current architecture authority.

## Contributors / AI workers

Human readers should use the portal and `PROJECT_STATUS.md`. Contributors and coding agents should read:

1. `AGENTS.md` — repository working rules
2. `CONTEXT.md` — compact agent/session continuity context
3. `SPEC.md` — current trusted contract and safety boundaries
4. `ROADMAP.md` — current and future milestones

## Public repository boundary

Treat repository content, Issues/PRs, Actions logs and Git history as public. Do not publish credentials, account IDs, private ARNs/endpoints, authentication data, session IDs, raw private findings or private screenshots.

## Status

**Demo v1 is frozen and validated; the MkDocs learning portal is live.** Current work is public-release cleanup and technical review, not expansion of AWS mutation scope.
