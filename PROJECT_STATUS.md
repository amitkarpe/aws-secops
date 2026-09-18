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
- `sec.astromedicomp.org` — AWS Compliance Agent with four-account read-only status + plan

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

`Config -> ops/sec read-only evidence -> G controls -> OIDC applies -> provider verifies -> Config converges`

- **G = ChatGPT / durable GitHub workflow control**
- **O = GitHub OIDC bounded mutation path**
- AWS Compliance Agent four-account tools = **read-only**
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

Issue #95 implementation PRs:

- #96 — live four-account ops/sec scope
- #97 — organization Config reader uses EC2 instance role, not legacy `AWS_PROFILE=vagent`
- #98 — retained deployment packaging includes planner dependencies

## Current next direction

The four-account SecOps demo is now the stable baseline.

A separate next experiment may compare the existing GitHub Actions + OIDC controller with GitHub App + AWS CodeConnections + CodeBuild. That CI/CD experiment must not weaken the proven SecOps trust boundary.

For restart state use `CONTEXT.md`; for product/security rules use `SPEC.md`.
