# Agent Context

Repository: `amitkarpe/aws-secops`  
Status: ACTIVE  
Updated: 2026-09-19

> Current-only restart state. GitHub and runtime readback take precedence over chat history.

## Current Authority

- Issue #106 / PR #107: management-facing Ops Operator Center GUI.
- Continue the same PR; do not create a replacement implementation PR.
- Scope is presentation and evidence clarity only. Backend APIs, Basic Auth, S3/SSH approvals, executor logic and AWS permissions remain unchanged.
- Validate GitHub first, then AWS MCP STS against the personal-LAB account specified in Issue #106, with `ap-southeast-1` explicitly selected. Stop AWS work on identity/authentication failure.

## Product Scope

- Exactly `lab-dev`, `lab-poc`, `lab-qa`, `lab-sec`.
- Exactly `s3-bucket-level-public-access-prohibited` and `restricted-ssh`.
- `ops.astromedicomp.org`: existing four-account organization Config evidence.
- `sec.astromedicomp.org`: status/plan plus the bounded Issue #100 native-approval executor.
- Retained 100-S3 / 10-SG behavior is legacy single-account scope only.
- Public/default output remains alias-only. No company/work/PROD scope.

## PR #107 Implementation

- Summary, exact four-account matrix, explanatory approval flow and historical acceptance cards.
- Refresh failure clears primary success; unknown states never count as compliant.
- Browser response age is explicitly not Config evaluation age.
- The existing backend acceptance record is historical GitHub OIDC proof, not a live audit feed.
- Legacy controls and advanced history are collapsed; existing confirmation behavior is preserved.
- Focused JavaScript behavior checks and synthetic desktop/mobile Chromium checks pass locally. See the PR for CI on the final head.
- Deployment and authenticated live verification are not yet recorded for this GUI revision. Do not infer rollout from a merge or a synthetic screenshot.

## Acceptance Background

Issue #100 records actual MCP S3 and SSH executions through fixed CodeBuild/CodeConnections, four provider-verified changes per control, Config convergence and the already-compliant guard. Its recorded Reject test withheld executor invocation after ASK; it was not a browser Reject-click test.

PR #105 remains the separate, open final acceptance documentation change. It records the final intentional reset to `NON_COMPLIANT x4` for both controls. That is historical expected demo state, not a fresh runtime observation. Reconcile its CONTEXT edits with this active Issue #106 pointer before any later merge.

Detailed prior evidence belongs in Issues #82, #88, #93, #95 and #100 and their PRs, not in this restart index.

## Safety

`Config -> read-only plan -> frozen exact batch -> native decision -> fixed CodeBuild/CodeConnections -> existing G/O controller -> exact target sessions -> provider readback -> independent Config convergence`

S3 and SSH remain separate approvals. No generic AWS administration, new controls, IAM/SCP changes or Config auto-remediation. Direct provider readback is remediation truth. Preserve manifests, journals and current access controls. X/Codex is fallback only.

## Next

Finish PR #107 review/CI, then perform only the authorized GUI rollout through the existing deployment path and record authenticated live verification on Issue #106. Keep the Issue open until that live acceptance is complete.

For the trusted execution contract, read `SPEC.md`.
