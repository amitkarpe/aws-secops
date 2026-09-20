# Project Status

**Current public baseline:** Compliance Agent v1 is live and E2E-verified in the four-account personal LAB. GitHub Release publication is the remaining v1 closure step.

## Current live scope

Aliases: `lab-dev`, `lab-poc`, `lab-qa`, `lab-sec`.

Controls:

1. `s3-bucket-level-public-access-prohibited`
2. `restricted-ssh`

Primary surfaces:

- `config.astromedicomp.org` — unified four-account Config Dashboard
- `sec.astromedicomp.org` — LibreChat / Compliance Agent v1
- `ops.astromedicomp.org` — redirect/legacy entry point

## Compliance Agent v1 — verified 2026-09-20

- unified Config backend: **PASS**, exactly 4 aliases × 2 controls = 8 checks;
- dedicated AgentCore Harness: **PASS**;
- five golden prompts: **PASS 5/5**;
- Harness reasoning boundary: **PASS** — no Harness tools;
- v1 shell remediation wiring: **IMPLEMENTING in Issue #138** — read + prepare + native-ASK execute;
- LibreChat visibility and authenticated user smoke: **PASS**;
- final direct MCP invocation: **PASS**;
- release publication: **PENDING**.

Architecture:

`LibreChat -> ask_compliance_agent_v1 -> Config backend -> AgentCore Harness -> answer`\n\nExplicit fix: `LibreChat -> prepare exact batch -> native Approve/Reject -> fixed CodeBuild/G/O executor -> provider readback -> Config convergence`

AgentCore Memory is not authoritative audit storage. Structured operational history remains separate; RAG is deferred until unstructured knowledge justifies it.

## Governed remediation — v1 execution boundary

Compliance Agent v1 now adopts the already-approved four-account remediation path:

`explicit fix -> frozen exact batch -> native Approve/Reject -> fixed CodeBuild/G/O path -> provider readback -> Config convergence`

No generic AWS mutation tool is exposed. Only the exact two-control prepare/executor contract is available, and execution remains human-approved.

## Current implementation priorities

1. close Issue #133 hardening: reproducible LibreChat ACL + real MCP startup regression + current-doc refresh;
2. publish GitHub Release `compliance-agent-v1.0.0` and close Issue #125;
3. evaluate Issue #130 as a **read-only** AWS MCP evidence source without widening mutation authority.

For restart state use `CONTEXT.md`; for product/security rules use `SPEC.md`.
