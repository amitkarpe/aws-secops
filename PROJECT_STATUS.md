# Project Status

**Current public baseline:** the four-account personal-LAB SecOps web demo is live and re-accepted end to end.

## Current live scope

Aliases:

- `lab-dev`
- `lab-poc`
- `lab-qa`
- `lab-sec`

Controls:

1. `s3-bucket-level-public-access-prohibited`
2. `restricted-ssh`

Primary web tools:

- `ops.astromedicomp.org` — live four-account Config matrix
- `sec.astromedicomp.org` — AWS Compliance Agent with four-account status, plan, and native Approve/Reject remediation for the exact two supported controls

The retained 100-S3 / 10-SG runtime remains available only as an explicitly labeled legacy single-account demo.

## Final live acceptance — 2026-09-18

| Control | Prepare | Reject | Approve | Provider | Config | Rerun |
|---|---|---:|---:|---|---|---|
| S3 BPA | SAFE_NONCOMPLIANT | 0 writes | 4 updates | VERIFIED | COMPLIANT x4 | ALREADY_COMPLIANT / 0 |
| Restricted SSH | SAFE_NONCOMPLIANT_UNATTACHED | 0 writes | 4 revocations | VERIFIED | COMPLIANT x4 | ALREADY_COMPLIANT / 0 |

The live web/API read side was verified at both ends of the run:

- before remediation: both controls `NON_COMPLIANT` across all four aliases;
- after provider-verified remediation and Config convergence: both controls `COMPLIANT` across all four aliases.

## Current architecture

`Config -> ops/sec -> frozen exact batch -> native approval -> CodeBuild/CodeConnections -> existing G/O controller -> provider verifies -> Config converges`

- **G = ChatGPT / durable GitHub workflow control**
- **O = GitHub OIDC bounded mutation path**
- AWS Compliance Agent status/plan tools = **read-only**; the exact executor is native `ASK` and is bound to one frozen control + batch.
- AWS MCP / Harness = **read-only unless separately bounded and explicitly authorized**
- direct provider readback = remediation truth
- Config = independent asynchronous evidence

## Trust boundary

- S3 and SG decisions remain independent.
- Reject performs zero writes.
- No Config automatic remediation.
- No SCP change was required for this demo.
- No generic model-accessible AWS administration tool exists.
- Default/public output is alias-only.
- Raw account IDs, ARNs, bucket names, SG IDs and credentials stay hidden.
- Personal LAB only.

## Current implementation

Completed:

- Issue #82 — multi-account provider E2E
- Issue #88 — organization Config bootstrap
- Issue #87 — management rehearsal
- Issue #93 — acceptance evidence added to web tools
- Issue #95 — web tools changed from retained single-account default to live four-account default
- Issue #100 — native chat approval + fixed CodeBuild/CodeConnections execution for S3 and SG; both controls live-accepted with 4 provider-verified changes and Config `COMPLIANT x4`

Issue #95 implementation PRs:

- #96 — live four-account ops/sec scope
- #97 — organization Config reader uses EC2 instance role, not legacy `AWS_PROFILE=vagent`
- #98 — retained deployment packaging includes planner dependencies

## Current next direction

The four-account SecOps demo is the stable baseline. The LAB resources are intentionally reset to `NON_COMPLIANT x4` for both controls for the next browser demo.

Next: improve the management-facing Operator Center GUI without changing the accepted trust boundary.

For restart state use `CONTEXT.md`; for product/security rules use `SPEC.md`.
