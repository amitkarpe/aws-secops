# AWS Compliance Agent

A public personal-lab project for **governed AWS compliance remediation**: AWS Config detects, an AI agent explains and plans, a human approves, AgentCore Gateway + Policy govern an exact tool, and direct AWS provider readback verifies the result.

> **Demo v1 is a learning/POC environment, not a production service.**

## Demo v1 at a glance

| | Proven demo scope |
|---|---|
| Resources | **100 S3 buckets + 10 unattached Security Groups** |
| Controls | **S3 Block Public Access + restricted SSH** |
| Approval | **Separate native human decision per action family** |
| Mutation | **Exact tools only; no generic AWS write tool** |
| Verification | **Direct provider readback; AWS Config converges independently** |

```text
AWS Config
   ↓
AWS Compliance Agent
   ↓
Human Approve / Reject
   ↓
AgentCore Gateway + Policy
   ↓
Exact S3 / Security Group tool
   ↓
AWS provider readback
```

The core security principle is simple:

> **The AI recommends the change; it does not authorize the change.**

## Start here

1. **Learning portal:** https://amitkarpe.github.io/aws-secops/
2. Read [Architecture](docs/architecture.md) for the control path.
3. Read [Demo v1](docs/demo-v1.md) for the end-to-end flow and safe prompts.
4. Read [Governance](docs/governance.md) for approval, Policy, exact-tool and verification boundaries.
5. Read [Learning path](docs/learning-path.md) for a guided tour of the deeper proofs and runbooks.

## What this project is — and is not

This project focuses on the gap **after detection**. It does not try to replace AWS Config, CloudTrail, CloudWatch, CloudSCAPE or VAPT tooling.

The agent is intentionally bounded:

- read-only questions must remain read-only;
- only supported, server-owned remediation families can be prepared;
- the model cannot choose arbitrary account, Region, API, resource IDs or AWS action at execution time;
- S3 and Security Group approvals remain independent;
- provider state, not model confidence, determines completion;
- `UNKNOWN`, `FAILED` and partial outcomes remain explicit.

## Repository map

```text
docs/implementation/   plans and implementation proofs
docs/operations/       runbooks, demo steps, cost and cleanup
docs/research/         AgentCore, cost and feasibility research
integration/           LibreChat / MCP / agent integration
pilot_v1/              bounded application and remediation logic
scripts/               deployment, proof and operator helpers
tests/                 deterministic regression tests
```

## Contributors / AI workers

Human readers should start with the portal above. Contributors and coding agents should read:

1. `AGENTS.md` — repository working rules
2. `CONTEXT.md` — current project truth
3. `SPEC.md` — current trusted contract and safety boundaries
4. `ROADMAP.md` — current and future milestones

## Public repository boundary

Treat repository content, Issues/PRs, Actions logs and Git history as public. Do not commit credentials, account IDs, private ARNs/endpoints, authentication data, session IDs, raw private findings or private screenshots.

## Status

**Demo v1: frozen and validated.** The next milestone is documentation/publication through MkDocs Material + GitHub Pages before adding more AWS controls.
