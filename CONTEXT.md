# Agent Context

Repository: `amitkarpe/aws-secops`  
Status: ACTIVE  
Updated: 2026-09-23

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
- immutable GitHub Release `compliance-agent-v1.0.0` published at commit `5d4121eb7e3621d04ae2e05c3b66fdd89879b7e0`;
- S3 authenticated Reject-only API E2E: 4/4 PASS;
- SSH authenticated Reject-only API E2E: 4/4 PASS;
- exact-exclusion authenticated Reject-only API E2E: 4/4 PASS, zero remediation-execution dispatches and zero AWS writes;
- manual browser Approve/Submit path exercised;
- rich-card width regression fixed and visually accepted;
- duplicate assistant next-action removed; native rich card owns the single next action;
- PRs #169, #163, #172 and #174 merged;
- stale PRs #105, #137 and #171 closed.

## Current Engineering Work

Compliance Agent v1 release closure is complete. Issues #141 and #125 are
closed, and Issue #173 has no remaining implementation scope.

Issue #170 remains the single roadmap. M1 completed in Issue #178 / PR #179,
M2 in Issue #180 / PR #181, M3A in Issue #182 / PR #183, M3B in Issue #184 /
PR #185, M4A in Issue #186 / PR #187, and M4B in Issue #188 / PR #189. Issue
#191 / PR #192 is the active live `s3_ssl` Reject-only milestone, using the
merged native decision receipt boundary from Issue #193 / PR #194. The
repo-owned runtime patch is deployed on the retained personal-LAB host; a fresh
post-restart read-only SSM status check on 2026-09-23 returned HTTP 200 with all
four registered aliases identity-verified and available, and a current
finding. It also confirmed both services active and the pinned resume patch
installed. AWS writes and remediation dispatches remain zero. Local regression
is green (336 repository tests, 24 Compliance Agent v1 tests, 19 native-decision
and browser-boundary Node tests), including duplicate/racing Reject,
durable receipt reopen/retry, timeout, scope mismatch, expiry and source-drift
cases. The authenticated native Reject E2E remains unaccepted: the dedicated
localhost-CDP Chrome profile is at login and requires ordinary human sign-in.
The isolated-profile Playwright runner now validates read-only status, exact
Reject-only card scope, one-shot native resume, persisted completion, no
executor dispatch, and conversation cleanup; it has not passed the live
authenticated journey yet.
Keep this path read-only, Reject-only and independent from Issue #176 / PR #177.
Do not add a third control or a live mutation path.

## Session Power

Follow `docs/operations/LAB_SESSION_POWER.md`.

- repository-only edits do not require a host start;
- runtime validation may use the same verified retained host;
- temporary auth/test data must be cleaned;
- automated E2E remains Reject-only;
- stop only on a real safety/access blocker;
- never terminate retained LAB infrastructure as routine cleanup.

## Next

Continue PR #192 in the existing worktree. After normal sign-in to the isolated
temporary Chrome profile, run the exact authenticated `s3_ssl` native Reject
journey, bounded live recovery checks, and cleanup; never choose Approve. Then
leave a sanitized review handoff. Do not merge or start Issue #170 M4 follow-up
work until its acceptance gates are explicitly complete.

## Restart

`Read AGENTS.md, CONTEXT.md, Issue #191 and PR #192. Continue only the live s3_ssl Reject-only milestone; no Approve or AWS writes.`
