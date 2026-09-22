# AWS Compliance Agent

A public personal-LAB project for **governed agentic AWS SecOps**.

> **Personal lab / POC only. Not a production service.**

## Current primary demo

Exactly four LAB aliases:

- `lab-dev`
- `lab-poc`
- `lab-qa`
- `lab-sec`

Exactly two supported controls:

1. S3 bucket-level Block Public Access
2. Security Group restricted SSH

Current Compliance Agent v1 path:

```text
Organization AWS Config
        ↓
Config Dashboard
        ↓
Compliance Agent v1
        ↓
strict loopback Config adapter (:1111)
        ↓
dedicated Amazon Bedrock AgentCore Harness
        ↓
Nova 2 Lite reasoning, no Harness tools
        ↓
read / explain / recommend in LibreChat

Explicit fix intent
        ↓
exact four-account batch preparation
        ↓
native Approve / Reject
        ↓
fixed CodeBuild + G/O controller
        ↓
provider readback + Config convergence
```

The core security principle remains:

> **The agent can detect, explain and prepare a supported fix; the human authorizes the exact batch, then the bounded executor applies and verifies it.**

## What is live-proven

| Capability | Current evidence |
|---|---|
| Four-account Config status | **LIVE** — exactly 4 aliases × 2 controls |
| Compliance Agent v1 | **LIVE** — Harness-backed reasoning + governed remediation integration |
| v1 golden prompts | **PASS 5/5** — status, explain, plan, fix guard, identifiers |
| v1 LibreChat smoke | **PASS** — selectable agent, expected MCP tool, four-account response |
| v1 MCP boundary | **PASS** — clean read tool plus exact prepare/executor integration; execution remains native-ASK gated |
| Four-account governed remediation proof | **PASS** — separate bounded approval/execution path with provider readback |
| S3/SSH Reject | **PASS** — 0 writes for the rejected exact batch |
| S3/SSH Approve | **PASS** — exact provider-verified changes |
| Config convergence | **PASS** — independent asynchronous evidence |

Latest clean v1 release acceptance: **2026-09-22**.

## Two agent paths

### Compliance Agent v1 — current specialist

- AgentCore Harness is the reasoning layer for evidence-grounded status/explanation/planning.
- Current evidence comes only from the unified Config backend.
- The same v1 LibreChat agent exposes the exact four-account prepare/executor tools for explicit fix intent.
- The Harness itself remains tool-free; mutation authority is outside the Harness.
- Native Approve/Reject is required before execution.
- Operational identifiers may be returned only when authorized evidence actually contains them.

### Governed remediation path

Compliance Agent v1 reuses the existing Issue #100 mutation contract rather than inventing a new executor:

```text
explicit fix intent
   ↓
frozen exact four-account plan
   ↓
native Approve / Reject
   ↓
fixed CodeBuild + existing G/O controller
   ↓
exact target sessions
   ↓
provider readback
   ↓
independent Config convergence
```

This is not a generic AWS administration path; it is the only remediation path inherited by Compliance Agent v1.

## Current web surfaces

- **Config Dashboard:** https://config.astromedicomp.org/
- **Compliance Agent / LibreChat:** https://sec.astromedicomp.org/
- `ops.astromedicomp.org` is retained only as a redirect/legacy entry point.

## Release state

Compliance Agent v1.0.0 is published from the exact validated release commit:

- release: [Compliance Agent v1.0.0](https://github.com/amitkarpe/aws-secops/releases/tag/compliance-agent-v1.0.0)
- tag: `compliance-agent-v1.0.0`
- release commit: `5d4121eb7e3621d04ae2e05c3b66fdd89879b7e0`
- in-repo release history: [agents/compliance-agent-v1/RELEASE_NOTES.md](agents/compliance-agent-v1/RELEASE_NOTES.md)
- canonical user-facing history: GitHub Releases

## Current evidence

- [Compliance Agent v1](agents/compliance-agent-v1/README.md)
- [Management audit view](docs/operations/MANAGEMENT_AUDIT_VIEW.md)
- [Architecture](docs/architecture.md)
- [Governance](docs/governance.md)
- [ChatGPT + GitHub OIDC + AWS MCP operating guide](docs/operations/CHATGPT_GITHUB_OIDC_AWS_MCP.md)
- [Project status](PROJECT_STATUS.md)
- [Demo v1](docs/demo-v1.md) — retained legacy/single-account detail

Key milestones:

- Issue #82 — four-account provider E2E
- Issue #88 — organization Config evidence
- Issue #100 — native governed four-account chat execution path
- Issue #120 — four-account demo re-arm + legacy Operator retirement
- Issues #123/#125 — clean Compliance Agent v1 + AgentCore Harness acceptance
- Issue #130 — next read-only AWS MCP evidence-source experiment
- Issue #186 — synthetic deterministic exception/audit substrate for the
  post-v1 roadmap; it is not a new live control or execution path
- Issue #188 — synthetic `s3_ssl` second-control governance proof; it reuses
  the bounded approval path and does not authorize live AWS mutation

## Important boundaries

- Personal LAB only; no Synapxe/work/office authority.
- Exactly four registered aliases and two supported controls for v1.
- Compliance Agent v1 may prepare and invoke only the exact four-account executor for the two supported controls.
- Governed mutation remains a separate authorization/execution boundary behind native human approval.
- Reject means zero writes for that exact batch.
- Provider readback proves remediation completion.
- AWS Config is independent asynchronous evidence.
- No generic model-accessible AWS administration tool is exposed.
- Never commit credentials, tokens, auth/session material, or private runtime evidence.

### Fresh ChatGPT operator session

Start a new chat with:

> `Using GitHub app - Read AGENTS.md, CONTEXT.md, active Issue/PR and continue.`

GitHub is the durable project source of truth.
