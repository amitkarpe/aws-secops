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

The current management/operator story is:

```text
Organization AWS Config
        ↓
ops.astromedicomp.org
        ↓
live four-account alias-only status
        ↓
sec.astromedicomp.org
AWS Compliance Agent
        ↓
read-only four-account status + plan
        ↓
explicit governed G/O execution path
        ↓
GitHub OIDC exact AWS change
        ↓
direct provider readback
        ↓
AWS Config converges independently
```

The core security principle remains:

> **The AI can investigate and recommend; it does not authorize an AWS change.**

## What is live-proven

| Capability | Current evidence |
|---|---|
| Four-account Config status | **LIVE** — both controls across exactly four aliases |
| Four-account Compliance Agent plan | **LIVE / read-only** — no multi-account chat executor |
| S3 Reject | **PASS** — 0 writes |
| S3 Approve | **PASS** — 4 exact provider-verified BPA updates |
| SG Reject | **PASS** — 0 writes |
| SG Approve | **PASS** — 4 exact provider-verified SSH revocations |
| Config convergence | **PASS** — both controls `COMPLIANT x4` |
| Idempotent rerun | **PASS** — `ALREADY_COMPLIANT`, 0 writes |
| Public-safe output | **PASS** — aliases only; raw AWS identifiers hidden |

The final four-account web/API acceptance was re-run on 2026-09-18 after Issue #95.

## Two execution boundaries

### Live four-account scope

The Compliance Agent can read current organization Config state and produce a four-account remediation plan.

It **cannot** execute a four-account mutation from chat.

Four-account writes remain on the separate governed path:

```text
G / GitHub durable decision
        ↓
O = GitHub OIDC
        ↓
exact target sessions
        ↓
bounded control-specific AWS action
        ↓
provider verification
```

### Legacy retained single-account demo

The earlier retained runtime still exists for engineering/history:

- 100 S3 demo buckets
- 10 unattached Security Groups
- native LibreChat approval + exact-tool flows

It is now explicitly **Legacy retained single-account demo** on the Operator page and is not the default answer for generic current-status or remediation-plan questions.

## Operator pages

- **Operations Console:** https://ops.astromedicomp.org/
  - primary: live four-account Config matrix
  - secondary: latest accepted E2E proof
  - legacy section: retained 100-S3 / 10-SG demo
- **AWS Compliance Agent:** https://sec.astromedicomp.org/
  - generic status -> live four-account status
  - generic plan -> live four-account plan
  - legacy retained tools only when explicitly requested

## 3-minute demo

Start with [Agentic SecOps — 3-minute demo](docs/operations/AGENTIC_DEMO_3_MIN.md).

Short story:

1. Show four aliases and both controls in the Operator page.
2. Ask the Compliance Agent for current status.
3. Ask for the four-account remediation plan.
4. Re-arm only through the governed operator/G/O path when a live non-compliant demo is required.
5. Prove Reject = 0 writes.
6. Prove Approve = exact provider-verified changes.
7. Show Config convergence to `COMPLIANT x4`.
8. Rerun and show `ALREADY_COMPLIANT` / 0 writes.

## Current evidence

- [Management audit view](docs/operations/MANAGEMENT_AUDIT_VIEW.md)
- [Architecture](docs/architecture.md)
- [Governance](docs/governance.md)
- [Operations Console direction](docs/operator-console.md)
- [Project status](PROJECT_STATUS.md)
- [Demo v1](docs/demo-v1.md) — retained legacy/single-account detail

Key milestones:

- Issue #82 / PRs #83–#84 — four-account provider E2E
- Issue #88 / PRs #89–#91 — organization AWS Config evidence
- Issue #87 / PR #92 — management rehearsal
- Issue #93 / PR #94 — acceptance evidence on ops/sec
- Issue #95 / PRs #96–#98 — live four-account ops/sec default scope

## Important boundaries

- Personal LAB only; no Synapxe/work/office authority.
- Exactly two supported controls.
- Four-account chat tools are read-only.
- Multi-account mutation remains on the separate governed GitHub OIDC path.
- Reject means zero writes for that exact batch.
- Provider readback proves remediation completion.
- AWS Config is independent asynchronous evidence.
- No generic model-accessible AWS administration tool is exposed.
- Public/default output hides account IDs, ARNs, bucket names, Security Group IDs and credentials.

### Fresh ChatGPT operator session

Start a new chat with:

> `Using GitHub app - Read AGENTS.md, CONTEXT.md, active Issue/PR and continue.`

GitHub is the durable project source of truth.
