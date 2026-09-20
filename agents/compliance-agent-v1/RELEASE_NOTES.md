# Compliance Agent Release Notes

This file is append-only product history for the clean Compliance Agent line.

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
- preserve privacy-safe alias-only output;
- refuse to bypass the approved mutation boundary.

### Planned acceptance

- Config/backend contract test;
- four-account MCP/tool test;
- five golden agent prompts;
- privacy/adversarial check;
- approval-boundary check;
- minimal LibreChat browser smoke;
- one final `DEMO READY / NOT READY` report.

### Known legacy defect being replaced

The current legacy Compliance Agent still routes `get_multi_account_status` through the retired Operator backend on loopback port 4444. Compliance Agent v1 will not reuse that implementation.

### Release evidence required before changing this status to RELEASED

- exact release commit;
- CI/test run;
- live proof date;
- acceptance summary;
- known limitations;
- rollback/reference commit.

---

## Release-note rule

For every later version append a new section and create a durable snapshot under:

`docs/releases/<product>-vX.Y.Z.md`

Do not rewrite prior released notes.
