# Agent Context

Repository: `amitkarpe/aws-secops`  
Status: ACTIVE  
Updated: 2026-09-20

> Current-only restart index. Read the latest owning Issue/PR comment for mutable rollout state; historical proof documents are not live truth.

## Current Authority

- Personal-LAB standing authority remains active.
- Keep the retained host running during active demo work unless Amit explicitly requests shutdown.
- Config Dashboard is the single active hosted dashboard.
- Exactly four registered LAB aliases and exactly two supported controls remain the current v1 scope.
- No company/PROD scope and no generic model-accessible AWS mutation.

## Current Product

### Compliance Agent v1

```text
LibreChat
  -> ask_compliance_agent_v1
  -> loopback unified Config backend (:1111)
  -> exact 4-account × 2-control evidence
  -> dedicated AgentCore Harness compliance_agent_v1
  -> Nova 2 Lite, no Harness tools
  -> read-only answer
```

Verified 2026-09-20:

- Config evidence: PASS 4 aliases × 2 controls = 8 checks;
- Harness golden prompts: PASS 5/5;
- installed MCP: PASS, exactly one tool;
- LibreChat agent visible/selectable for Amit: PASS;
- authenticated LibreChat status prompt: PASS;
- final direct MCP invocation: PASS, `mutation=false`.

Issue #125 remains open only for release closure.

### Governed remediation

The separate Issue #100 path remains the bounded mutation boundary:

`explicit fix -> frozen exact batch -> native decision -> fixed CodeBuild/G/O path -> exact target sessions -> provider readback -> Config convergence`

Compliance Agent v1 does not inherit this execution authority.

## Current Engineering Work

Issue #133 hardens the verified v1 baseline:

1. reproducible fail-closed LibreChat ACL helper;
2. real stdio MCP startup/list-tools regression;
3. current README/STATUS/ROADMAP/CONTEXT refresh.

A prepared release branch also exists, but GitHub Release publication has not yet completed.

## Session Power

Follow [Personal LAB session power](docs/operations/LAB_SESSION_POWER.md).

- repository-only edits do not require a host start;
- runtime validation may use the same verified retained host;
- stop only on Amit's explicit cost-saving request;
- never terminate.

## Next

Finish Issue #133 review/CI/live idempotency proof, merge it, then publish and verify `compliance-agent-v1.0.0` before closing Issue #125.
