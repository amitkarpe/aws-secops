# Project Status

**Current public baseline:** Compliance Agent v1.0.0 is released and E2E-verified in the four-account personal LAB.

Release: [Compliance Agent v1.0.0](https://github.com/amitkarpe/aws-secops/releases/tag/compliance-agent-v1.0.0) at `5d4121eb7e3621d04ae2e05c3b66fdd89879b7e0`.

## Current live scope

Aliases: `lab-dev`, `lab-poc`, `lab-qa`, `lab-sec`.

Controls:

1. `s3-bucket-level-public-access-prohibited`
2. `restricted-ssh`

Primary surfaces:

- `config.astromedicomp.org` — unified four-account Config Dashboard
- `sec.astromedicomp.org` — LibreChat / Compliance Agent v1
- `ops.astromedicomp.org` — redirect/legacy entry point

## Compliance Agent v1 — released 2026-09-22

- unified Config backend: **PASS**, exactly 4 aliases × 2 controls = 8 checks;
- dedicated AgentCore Harness: **PASS**;
- five golden prompts: **PASS 5/5**;
- Harness reasoning boundary: **PASS** — no Harness tools;
- v1 shell remediation wiring: **PASS** — read + prepare + native-ASK execute;
- LibreChat visibility and authenticated user smoke: **PASS**;
- final direct MCP invocation: **PASS**;
- authenticated S3 and SSH Reject-only E2E: **PASS 4/4 each**;
- exact-exclusion Reject-only E2E: **PASS 4/4**, zero execution dispatches and zero AWS writes;
- release publication and exact tag target: **PASS**.

Architecture:

`LibreChat -> ask_compliance_agent_v1 -> Config backend -> AgentCore Harness -> answer`

Explicit fix: `LibreChat -> prepare exact batch -> native Approve/Reject -> fixed CodeBuild/G/O executor -> provider readback -> Config convergence`

AgentCore Memory is not authoritative audit storage. Structured operational history remains separate; RAG is deferred until unstructured knowledge justifies it.

## Governed remediation — v1 execution boundary

Compliance Agent v1 now adopts the already-approved four-account remediation path:

`explicit fix -> frozen exact batch -> native Approve/Reject -> fixed CodeBuild/G/O path -> provider readback -> Config convergence`

No generic AWS mutation tool is exposed. Only the exact two-control prepare/executor contract is available, and execution remains human-approved.

## Next roadmap

Issue #170 is the single future roadmap. Its M1 sanitized private-capability
adapter is not started. No catalog, 1K query/export, bulk remediation, or new
control implementation is part of the v1.0.0 release closure.

For restart state use `CONTEXT.md`; for product/security rules use `SPEC.md`.
