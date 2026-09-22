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
- duplicate assistant next-action removed; native rich card owns the single next action;
- PRs #169, #163 and #172 merged;
- stale PRs #105, #137 and #171 closed.

## Current Engineering Work

Issue #173 is the active **Codex reset sprint** for Issue #170 M0 release closure.

Sprint milestones:
1. close Issue #141 explicit exception-batch Reject evidence;
2. freeze the current validated v1 release candidate;
3. publish a fresh `compliance-agent-v1.0.0` release from current truth;
4. close v1 release work and leave Issue #170 as the only future roadmap.

Do not start Issue #170 M1+ implementation in this sprint.

## Session Power

Follow `docs/operations/LAB_SESSION_POWER.md`.

- repository-only edits do not require a host start;
- runtime validation may use the same verified retained host;
- temporary auth/test data must be cleaned;
- automated E2E remains Reject-only;
- stop only on a real safety/access blocker;
- never terminate retained LAB infrastructure as routine cleanup.

## Next

Continue Issue #173 / its active PR end-to-end. Codex should not wait for Amit between routine steps.

## Restart

`Read AGENTS.md, CONTEXT.md, Issue #173 and the active PR. Own the Codex reset sprint until acceptance or a real stop gate.`
