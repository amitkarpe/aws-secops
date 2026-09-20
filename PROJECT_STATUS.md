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
- read-only / no-mutation boundary: **PASS**;
- installed MCP bridge: **PASS**, exactly one tool;
- LibreChat visibility and authenticated user smoke: **PASS**;
- final direct MCP invocation: **PASS**;
- release publication: **PENDING**.

Architecture:

`LibreChat -> compliance_agent_v1 MCP -> unified Config backend -> AgentCore Harness -> Nova 2 Lite -> answer`

AgentCore Memory is not authoritative audit storage. Structured operational history remains separate; RAG is deferred until unstructured knowledge justifies it.

## Governed remediation — separate boundary

The approved four-account remediation path remains separate from Compliance Agent v1:

`explicit fix -> frozen exact batch -> native Approve/Reject -> fixed CodeBuild/G/O path -> provider readback -> Config convergence`

No generic AWS mutation tool is exposed to the model.

## Current implementation priorities

1. close Issue #133 hardening: reproducible LibreChat ACL + real MCP startup regression + current-doc refresh;
2. publish GitHub Release `compliance-agent-v1.0.0` and close Issue #125;
3. evaluate Issue #130 as a **read-only** AWS MCP evidence source without widening mutation authority.

For restart state use `CONTEXT.md`; for product/security rules use `SPEC.md`.
