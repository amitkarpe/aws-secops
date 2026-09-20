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

Current clean read path:

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
read-only answer in LibreChat
```

The core security principle remains:

> **The AI can investigate and recommend; it does not authorize an AWS change.**

## What is live-proven

| Capability | Current evidence |
|---|---|
| Four-account Config status | **LIVE** — exactly 4 aliases × 2 controls |
| Compliance Agent v1 | **LIVE** — AgentCore Harness-backed, read-only |
| v1 golden prompts | **PASS 5/5** — status, explain, plan, fix guard, identifiers |
| v1 LibreChat smoke | **PASS** — selectable agent, expected MCP tool, four-account response |
| v1 MCP boundary | **PASS** — exactly one tool, no mutation capability |
| Four-account governed remediation proof | **PASS** — separate bounded approval/execution path with provider readback |
| S3/SSH Reject | **PASS** — 0 writes for the rejected exact batch |
| S3/SSH Approve | **PASS** — exact provider-verified changes |
| Config convergence | **PASS** — independent asynchronous evidence |

Latest clean v1 live acceptance: **2026-09-20**.

## Two agent paths

### Compliance Agent v1 — current clean specialist

- AgentCore Harness is the reasoning layer.
- Current evidence comes only from the unified Config backend.
- v1 exposes one read-only MCP tool: `ask_compliance_agent_v1`.
- v1 does **not** execute remediation.
- Operational identifiers may be returned only when the authorized evidence actually contains them.

### Governed remediation path — separate bounded capability

The existing AWS Compliance Agent / Issue #100 path preserves the approved mutation contract:

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

This is not a generic AWS administration path and is not inherited by Compliance Agent v1.

## Current web surfaces

- **Config Dashboard:** https://config.astromedicomp.org/
- **Compliance Agent / LibreChat:** https://sec.astromedicomp.org/
- `ops.astromedicomp.org` is retained only as a redirect/legacy entry point.

## Release state

The clean v1 baseline is verified and ready for tag/release:

- planned tag: `compliance-agent-v1.0.0`
- in-repo release history: [agents/compliance-agent-v1/RELEASE_NOTES.md](agents/compliance-agent-v1/RELEASE_NOTES.md)
- canonical user-facing history: GitHub Releases
- GitHub Release publication is still pending while Issue #125 remains open.

## Current evidence

- [Compliance Agent v1](agents/compliance-agent-v1/README.md)
- [Management audit view](docs/operations/MANAGEMENT_AUDIT_VIEW.md)
- [Architecture](docs/architecture.md)
- [Governance](docs/governance.md)
- [Project status](PROJECT_STATUS.md)
- [Demo v1](docs/demo-v1.md) — retained legacy/single-account detail

Key milestones:

- Issue #82 — four-account provider E2E
- Issue #88 — organization Config evidence
- Issue #100 — native governed four-account chat execution path
- Issue #120 — four-account demo re-arm + legacy Operator retirement
- Issues #123/#125 — clean Compliance Agent v1 + AgentCore Harness acceptance
- Issue #130 — next read-only AWS MCP evidence-source experiment

## Important boundaries

- Personal LAB only; no Synapxe/work/office authority.
- Exactly four registered aliases and two supported controls for v1.
- Compliance Agent v1 is read-only and has no execution tool.
- Governed mutation remains a separate exact approval/execution path.
- Reject means zero writes for that exact batch.
- Provider readback proves remediation completion.
- AWS Config is independent asynchronous evidence.
- No generic model-accessible AWS administration tool is exposed.
- Never commit credentials, tokens, auth/session material, or private runtime evidence.

### Fresh ChatGPT operator session

Start a new chat with:

> `Using GitHub app - Read AGENTS.md, CONTEXT.md, active Issue/PR and continue.`

GitHub is the durable project source of truth.
