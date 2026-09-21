# Agent Context

Repository: `amitkarpe/aws-secops`  
Status: ACTIVE  
Updated: 2026-09-21

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
  -> grounded answer

Explicit fix
  -> prepare_multi_account_remediation
  -> native Approve / Reject
  -> execute_multi_account_remediation
  -> fixed CodeBuild/G/O path
  -> provider readback + Config convergence
```

Verified 2026-09-20:

- Config evidence: PASS 4 aliases × 2 controls = 8 checks;
- Harness golden prompts: PASS 5/5;
- installed read MCP: PASS; v1 remediation wiring is Issue #138;
- LibreChat agent visible/selectable for Amit: PASS;
- authenticated LibreChat status prompt: PASS;
- final direct MCP invocation: PASS, `mutation=false`.

Issue #125 remains open only for release closure.

### Governed remediation

The separate Issue #100 path remains the bounded mutation boundary:

`explicit fix -> frozen exact batch -> native decision -> fixed CodeBuild/G/O path -> exact target sessions -> provider readback -> Config convergence`

Issue #138 makes this exact execution authority available through the same Compliance Agent v1 shell; the Harness itself remains tool-free.

## Current Engineering Work

Issue #161 / Draft PR #160 is the active authority. It adds four authenticated
LibreChat HTTP API gates for the real Compliance Agent v1 path and the smallest
backend-only approval-description compatibility correction exposed by those
gates. Automated acceptance submits Reject only and must prove zero remediation
writes plus cleanup of ephemeral test auth/data.

## Session Power

Follow [Personal LAB session power](docs/operations/LAB_SESSION_POWER.md).

- repository-only edits do not require a host start;
- runtime validation may use the same verified retained host;
- stop only on Amit's explicit cost-saving request;
- never terminate.

## Next

Finish all four Issue #161 retained-LAB API gates, publish sanitized PASS/FAIL
evidence on Issue #161, and leave `HANDOFF: CHATGPT` on Draft PR #160 for final
review and browser visual acceptance. Do not merge.
