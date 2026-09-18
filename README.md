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
live four-account evidence
        ↓
sec.astromedicomp.org
AWS Compliance Agent
        ↓
read-only plan
        ↓
freeze exact control + four-account batch
        ↓
native LibreChat Approve / Reject
        ↓
fixed AWS CodeBuild project
GitHub App + AWS CodeConnections
        ↓
existing G/O controller role
        ↓
exact target sessions
        ↓
bounded AWS change
        ↓
direct provider readback
        ↓
AWS Config converges independently
```

The core security principle remains:

> **The AI can investigate and recommend; the human approval binds one exact remediation batch.**

## What is live-proven

| Capability | Current evidence |
|---|---|
| Four-account Config status | **LIVE** — both controls across exactly four aliases |
| Four-account Compliance Agent plan | **LIVE / read-only** |
| Native approval | **LIVE** — separate S3 and SG ASK cards |
| S3 Reject | **PASS** — 0 CodeBuild execution dispatch |
| S3 Approve | **PASS** — 4 exact provider-verified BPA updates |
| SG Reject | **PASS** — 0 CodeBuild execution dispatch |
| SG Approve | **PASS** — 4 exact provider-verified SSH revocations |
| Source path | **PASS** — GitHub App + AWS CodeConnections |
| Execution path | **PASS** — fixed CodeBuild project -> existing G/O controller |
| Config convergence | **PASS** — both controls `COMPLIANT x4` |
| Idempotent guard | **PASS** — compliant state cannot prepare a new batch |
| Public-safe output | **PASS** — aliases only; raw AWS identifiers hidden |

Issue #100 was live-accepted on 2026-09-18.

## Native chat flow

For the default four-account scope:

1. Ask for current status.
2. Ask for the remediation plan.
3. Ask to fix one supported control.
4. The agent freezes one exact four-account batch.
5. LibreChat shows **Approve / Reject**.
6. Reject causes zero execution dispatch.
7. Approve sends only that frozen batch to the fixed CodeBuild executor.
8. Direct S3/EC2 readback proves the result.
9. AWS Config converges independently.

S3 and SG always require separate approvals.

## Operator pages

- **Operations Console:** https://ops.astromedicomp.org/
  - primary: live four-account Config matrix;
  - secondary: accepted E2E evidence;
  - legacy: retained 100-S3 / 10-SG demo.
- **AWS Compliance Agent:** https://sec.astromedicomp.org/
  - current status -> live four-account status;
  - plan -> live four-account plan;
  - explicit fix -> native approval + fixed CodeBuild executor.

## Demo starting state

After final acceptance the four LAB demo resources were re-armed:

- S3: `NON_COMPLIANT x4`;
- restricted SSH: `NON_COMPLIANT x4`.

This is intentional so the next browser demo can exercise the real approval path.

## Evidence

- [Management audit view](docs/operations/MANAGEMENT_AUDIT_VIEW.md)
- [3-minute demo](docs/operations/AGENTIC_DEMO_3_MIN.md)
- [Architecture](docs/architecture.md)
- [Governance](docs/governance.md)
- [Operations Console direction](docs/operator-console.md)
- [Project status](PROJECT_STATUS.md)

Key milestones:

- Issue #82 / PRs #83–#84 — four-account provider E2E.
- Issue #88 / PRs #89–#91 — organization AWS Config evidence.
- Issue #87 / PR #92 — management rehearsal.
- Issue #93 / PR #94 — acceptance evidence on ops/sec.
- Issue #95 / PRs #96–#99 — live four-account ops/sec default scope.
- Issue #100 / PRs #101–#104 — native chat approval + CodeBuild/CodeConnections execution.

## Important boundaries

- Personal LAB only; no Synapxe/work/office authority.
- Exactly two supported controls.
- No generic model-accessible AWS administration tool.
- Chat never selects arbitrary account IDs, resource IDs, role, Region, repository, branch, buildspec, AWS API, CIDR or port.
- Reject means no execution dispatch.
- Provider readback proves remediation completion.
- AWS Config is independent asynchronous evidence.
- No Config automatic remediation.
- No SCP change.
- Public/default output hides account IDs, ARNs, bucket names, Security Group IDs and credentials.

### Fresh ChatGPT operator session

Start a new chat with:

> `Using GitHub app - Read AGENTS.md, CONTEXT.md, active Issue/PR and continue.`

GitHub is the durable project source of truth.
