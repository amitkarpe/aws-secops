# Agent Context

Repository: `amitkarpe/aws-secops`  
Status: ACTIVE  
Updated: 2026-09-24

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
repo-owned runtime patch is deployed on the retained personal-LAB host. A fresh
post-restart read-only SSM status check on 2026-09-23 returned HTTP 200 with all
four registered aliases identity-verified and available, and a current
finding. A new sanitized SSM preflight verified `amit` is bound to the retained
SecOps host (both `aws-secops-bulk` and `aws-secops-librechat` active; operator
process explicitly uses `amit`). The pinned resume patch remains installed.
The `vagent` profile resolved to a different member-account EC2 and was not
used for this work.

The authenticated native E2E reached the exact s3_ssl card: one Reject, zero
Approve. Reject was selected and submitted once through the normal LibreChat
client. The final clean Playwright run returned PASS with native resume HTTP
200, the card detached, and rendered completion acknowledged the Reject
receipt without claiming an AWS change. The runtime returns success only after
durable `REJECTED` receipt persistence, `downstream_dispatches=0`, `aws_writes=0`, and
a fresh provider readback records `UNCHANGED`; Approve was absent and never
invoked. The exact completed test chat was archived through the authenticated
native Archive action (HTTP 200, exact conversation bound); Delete was never
invoked.

The first run's final assertion was overly specific about agent wording and
marked this successful receipt-gated completion as a false-negative. The runner
now accepts a rendered Reject/receipt acknowledgement and resumes an
already-selected Reject without clicking it twice. Focused browser contract
tests pass 12/12. Full repository regression passes 336 tests (4 skipped);
Compliance Agent v1 passes 24/24, and native receipt/browser Node tests pass
23/23. No AWS resource writes, Approve, remediation executor dispatch, or
cross-account mutation occurred. Finish bounded failure/recovery checks,
refresh exact-head CI, and post one sanitized handoff to PR #192; do not merge.
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

Continue PR #192 in the existing worktree. Complete full regression and
bounded failure/recovery checks, verify exact-head CI, then update the PR with
sanitized evidence. The authenticated `s3_ssl` native Reject and exact Archive
journeys are now proven. Never choose Approve, merge, or start Issue #170 M4
follow-up work until all acceptance gates are explicitly complete.

## Restart

`Read AGENTS.md, CONTEXT.md, Issue #191 and PR #192. Continue the full regression and bounded failure/recovery checks for the completed native s3_ssl Reject proof. No Approve, Delete, merge, or AWS writes.`
