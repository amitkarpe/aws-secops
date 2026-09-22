# Issue #193 — native decision receipt worktree

Parent: Issue #193  
Blocked milestone: Issue #191 / PR #192  
Base: current `main`

## M1 result

LibreChat v0.8.8-rc1 has no supported final-decision hook.

The configured tool-approval hook runs before the native approval card. The
authenticated resume controller validates and consumes the final decision, then
the single winning resume claim continues the agent.

Candidate seam:

`ResumeAgentController -> validated final decision -> successful approval CAS -> receipt callback -> resumeCompletion`

This seam is version-pinned to LibreChat v0.8.8-rc1 and must fail closed.

## M2 design contract

Implement one repo-owned, version-pinned patch installer plus one decision
receipt endpoint/adapter.

The patch may observe only the exact final native decision after all existing
LibreChat owner/tenant/action/generation/TTL/decision validation has passed and
after the caller wins the single approval CAS.

For the exact configured reject-only tool only, send a server-owned receipt
containing the minimum authoritative fields needed to bind the decision:

- tool identity;
- control key;
- batch ID;
- scope hash;
- action identity;
- generation identity;
- authenticated user identity binding;
- final decision;
- decision timestamp.

Do not accept arbitrary resource IDs, AWS operations, role names, account IDs,
URLs, or model-supplied execution parameters.

## Transaction / failure rule

The receipt is part of the decision transaction boundary.

For the reject-only tool:

1. native decision validates;
2. the caller wins the existing single-resume CAS;
3. durable receipt must persist;
4. only then may the controller continue.

If durable receipt persistence fails:

- do not call `resumeCompletion`;
- do not dispatch any tool;
- do not attempt an automatic second decision;
- surface a bounded fail-closed state;
- preserve enough generation/action identity for read-only reconciliation;
- duplicate client submits must not create duplicate receipts or execution.

A fire-and-forget callback is not acceptable.

## M3 fail-closed execution contract

Introduce a server-owned capability equivalent to:

`LIVE_EXECUTION_AUTHORIZED = false`

For `s3_ssl` under Issue #191:

- Reject -> durable `REJECTED`, zero execution dispatch;
- Approve -> durable `APPROVE_BLOCKED` / `LIVE_EXECUTION_NOT_AUTHORIZED`,
  zero execution dispatch;
- CodeBuild/Gateway/Lambda/AWS mutation paths are unreachable.

Do not alias `s3_ssl` to the existing S3 BPA execution family.

## Existing paths must remain unchanged

The patch must bypass all existing S3 BPA and restricted-SSH native approval
flows unless they are the exact configured reject-only tool.

No second approval UI is permitted.

## Required tests before deployment

- valid Reject receipt persists exactly once;
- valid Approve records BLOCKED exactly once;
- receipt write failure prevents continuation;
- duplicate/racing resume submissions produce one durable result;
- stale action/generation is rejected;
- wrong tool/control/batch/scope is rejected;
- restart/reopen retains receipt;
- existing S3 BPA approval path unchanged;
- existing restricted-SSH approval path unchanged;
- no CodeBuild/Gateway/Lambda dispatch for reject-only tool;
- zero AWS writes for reject-only tool.

## Deployment boundary

Repository implementation and deterministic tests first.

Do not deploy the patch until the exact-head test suite is green and the diff
shows the patch is limited to the version-pinned LibreChat resume seam plus the
repo-owned decision-receipt backend/installer.

No AWS mutation, IAM/OIDC/network change, new account/control, company/PROD
scope, or live s3_ssl remediation is authorized.

## Return condition

Post `HANDOFF: CHATGPT` on Issue #193 with:

- exact head SHA;
- files changed;
- deterministic test results;
- proof that existing BPA/SSH paths bypass the new callback unchanged;
- proof that Reject and Approve both have zero downstream dispatch for the
  reject-only tool;
- deployment readiness or the exact remaining stop gate.
