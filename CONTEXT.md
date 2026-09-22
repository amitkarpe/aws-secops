# Agent Context

Repository: `amitkarpe/aws-secops`  
Status: ACTIVE  
Updated: 2026-09-22

> Current-only restart index. Read the latest owning Issue/PR comment for mutable rollout state; historical proof documents are not live truth.

## Current Authority

- Personal-LAB standing authority remains active.
- Keep the retained host running during active demo work unless Amit explicitly requests shutdown.
- Exactly four registered LAB aliases and exactly two supported controls remain the current v1 scope.
- No company/PROD scope and no generic model-accessible AWS mutation.

## Current Product

Compliance Agent v1 is the stable four-account/two-control baseline:

`Status -> explain/prepare -> native Approve/Reject -> bounded execute -> AWS service readback -> Config evaluation`

Accepted current evidence:
- S3 authenticated Reject-only API E2E: 4/4 PASS;
- SSH authenticated Reject-only API E2E: 4/4 PASS;
- manual browser Approve/Submit path exercised;
- rich-card width regression fixed and visually accepted;
- PR #169 and PR #163 merged;
- stale PRs #105, #137 and #171 closed.

## Current Engineering Work

Issue #170 owns the roadmap.

Current gate is **M0 — close Compliance Agent v1**.

Remaining closure work:
1. remove duplicate next-action text outside the rich card;
2. refresh reproducible v1 release evidence against current main;
3. publish/record one current v1 release baseline;
4. close stale completed v1 Issues after evidence is durable.

Do not start #170 M1+ implementation until M0 is complete.

## Session Power

Follow `docs/operations/LAB_SESSION_POWER.md`.

- repository-only edits do not require a host start;
- runtime validation may use the same verified retained host;
- stop only on Amit's explicit cost-saving request;
- never terminate.

## Next

Finish Issue #170 M0 autonomously. After M0 is closed, leave #170 as the single active future roadmap and stop before M1 implementation.
