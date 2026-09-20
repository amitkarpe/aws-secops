# Compliance Agent Release Notes

This file is the in-repo source/history for the clean Compliance Agent line.

**Canonical user-facing release history:** GitHub Releases, following the same product-history style as projects such as OpenAI Codex.

## v1.0.0 — VERIFIED / RELEASE PENDING

Tag: `compliance-agent-v1.0.0`

Status: **VERIFIED — GitHub Release not yet published**

Owning Issue: #123

### Goal

Replace the broken legacy status path with a clean isolated Compliance Agent that reads the unified four-account Config backend and can be tested automatically without Amit manually exercising LibreChat.

### Implementing architecture

- dedicated AgentCore Harness `compliance_agent_v1`;
- Nova 2 Lite, Memory disabled, no Harness tools;
- strict local adapter reads only the unified Config backend;
- one new LibreChat MCP bridge and one new named `Compliance Agent v1` shell;
- no dependency on retired port 4444 or legacy `pilot_v1.compliance_mcp`.

### Planned user-visible capabilities

- current S3 Block Public Access status across four LAB aliases;
- current restricted SSH status across four LAB aliases;
- explain findings;
- produce a no-change remediation plan;
- return operational identifiers when authorized backend/tool responses provide them;
- refuse to bypass the approved mutation boundary.

### Verified acceptance

- Config backend: PASS — four registered aliases, two controls, eight checks;
- dedicated AgentCore Harness invocation: PASS;
- five golden prompts: PASS 5/5;
- identifier fidelity: PASS — unavailable identifiers were not fabricated;
- approval/execution boundary: PASS — v1 remained read-only;
- installed MCP bridge: PASS — one tool only, `ask_compliance_agent_v1`;
- LibreChat registration: PASS — `Compliance Agent v1` exists with only the v1 MCP tool;
- GitHub regression CI: PASS — workflow run 236;
- live proof date: 2026-09-20;
- exact verified commit: `8779cf9bd771be296b7983bf20e3881de3e10e48`.

Remaining before RELEASED:
- authenticated LibreChat UI/API smoke;
- publish GitHub Release `compliance-agent-v1.0.0`.

### Known legacy defect being replaced

The current legacy Compliance Agent still routes `get_multi_account_status` through the retired Operator backend on loopback port 4444. Compliance Agent v1 will not reuse that implementation.

### Release evidence required before changing this status to RELEASED

Publish a GitHub Release tagged `compliance-agent-v1.0.0` containing:

- Highlights;
- AgentCore Harness/runtime architecture;
- backend/tool contract changes;
- exact release commit;
- CI/acceptance run;
- live proof date;
- known limitations;
- rollback/reference commit.

---

## Release-note rule

For every later version append a new section here and publish a new immutable GitHub Release.

Do not rewrite prior published release notes.

### Identifier policy clarification

v1 does not require alias-only masking. Account/resource identifiers may be returned when they are present in authorized tool/backend responses. The agent must not fabricate missing identifiers and must never expose credentials, secrets, tokens or auth/session material.
