# Compliance Agent Release Notes

This file is the in-repo source/history for the clean Compliance Agent line.

**Canonical user-facing release history:** GitHub Releases, following the same product-history style as projects such as OpenAI Codex.

## v1.0.0 — VERIFIED / RELEASE PENDING

Tag: `compliance-agent-v1.0.0`

Status: **IMPLEMENTING REMEDIATION — GitHub Release not yet published**

Owning Issue: #123

### Goal

Replace the broken legacy status path with a clean isolated Compliance Agent that reads the unified four-account Config backend and can be tested automatically without Amit manually exercising LibreChat.

### Verified architecture

- dedicated AgentCore Harness `compliance_agent_v1`;
- Nova 2 Lite, Memory disabled, no Harness tools;
- strict local adapter reads only the unified Config backend;
- one clean Harness-backed read MCP bridge and one named `Compliance Agent v1` shell;\n- explicit fix intent reuses the accepted four-account planner/executor from Issue #100;\n- native Approve/Reject remains mandatory before the exact CodeBuild/G/O execution;\n- no dependency on legacy `pilot_v1.compliance_mcp` for the v1 read path.

### Verified user-visible capabilities

- current S3 Block Public Access status across four LAB aliases;
- current restricted SSH status across four LAB aliases;
- explain findings;
- produce a no-change remediation plan;
- return operational identifiers when authorized backend/tool responses provide them;
- fix one supported control after exact native human approval;\n- fix both supported controls only as two independent approval decisions;\n- reject/cancel with zero CodeBuild dispatch.

### Verified acceptance

- Config backend: PASS — four registered aliases, two controls, eight checks;
- dedicated AgentCore Harness invocation: PASS;
- five golden prompts: PASS 5/5;
- identifier fidelity: PASS — unavailable identifiers were not fabricated;
- Harness reasoning boundary: PASS — no Harness tools;\n- governed execution contract: wiring under Issue #138 using the already accepted Issue #100 four-account executor;
- installed MCP bridge: PASS — one tool only, `ask_compliance_agent_v1`;
- LibreChat registration and ACL visibility: PASS — `Compliance Agent v1` is selectable by the authorized user;
- authenticated LibreChat UI smoke: PASS — the expected v1 MCP tool ran and returned four-account evidence;
- direct installed read-MCP invocation: PASS — `mutation=false`;\n- release remediation tools: exact prepare + native-ASK execute, no generic AWS administration;
- live proof date: 2026-09-20;
- pre-hardening verified baseline: `d2c4125b712ccddd675c3c34a1284aaa7d503afc`;
- release hardening candidate: Issue #133 / PR #134.

Remaining before RELEASED:\n- complete Issue #138 live Reject + Approve acceptance for S3 and restricted SSH through Compliance Agent v1;\n- publish and verify GitHub Release `compliance-agent-v1.0.0` from the final remediation-tested commit.

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
