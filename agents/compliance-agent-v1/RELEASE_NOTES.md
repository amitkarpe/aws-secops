# Compliance Agent Release Notes

This file is the in-repo source/history for the clean Compliance Agent line.

**Canonical user-facing release history:** GitHub Releases, following the same product-history style as projects such as OpenAI Codex.

## v1.0.0 — PLANNED

Tag: `compliance-agent-v1.0.0`

Status: **Not released**

Owning Issue: #123

### Goal

Replace the broken legacy status path with a clean isolated Compliance Agent that reads the unified four-account Config backend and can be tested automatically without Amit manually exercising LibreChat.

### Planned user-visible capabilities

- current S3 Block Public Access status across four LAB aliases;
- current restricted SSH status across four LAB aliases;
- explain findings;
- produce a no-change remediation plan;
- return operational identifiers when authorized backend/tool responses provide them;
- refuse to bypass the approved mutation boundary.

### Planned acceptance

- Config/backend contract test;
- four-account MCP/tool test;
- AgentCore Harness availability/invocation test;
- five golden Harness prompts;
- identifier-fidelity check;
- approval-boundary check;
- minimal LibreChat browser smoke;
- one final `DEMO READY / NOT READY` report.

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
