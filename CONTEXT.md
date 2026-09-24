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
repo-owned runtime patch is deployed on the retained personal-LAB host; a fresh
post-restart read-only SSM status check on 2026-09-23 returned HTTP 200 with all
four registered aliases identity-verified and available, and a current
finding. It also confirmed both services active and the pinned resume patch
installed. AWS writes and remediation dispatches remain zero. Local regression
was green before the current runner update (336 repository tests, 24
Compliance Agent v1 tests, 19 native-decision and browser-boundary Node tests),
including duplicate/racing Reject, durable receipt reopen/retry, timeout, scope
mismatch, expiry and source-drift cases. Issue #195 source/runtime analysis
found that the previous Playwright runner used page-level `fetch` calls that
omitted LibreChat's `Authorization` header; LibreChat's normal client sets that
header through its authenticated request helper. Thus the runner's direct
status/history/cleanup requests received 401, while normal UI client calls
succeeded. No runtime auth or proxy change is indicated. The runner now waits
for rendered UI state, records only sanitized response metadata, verifies a
normal authenticated history reload, and performs conversation deletion only
through LibreChat's native UI. The focused contract suite passes 8/8 after this
change. A normal auth refresh and history reload returned HTTP 200, but the
native DELETE returned 401 once and 500 after refresh. Redacted SSM log
aggregation attributes the 500 to the conversation-store delete stage but
exposes no safe exception class. The exact read-only diagnostic remains
visible in the UI; cleanup is not claimed. No approval, executor dispatch, or
AWS resource write occurred. Authenticated Reject acceptance remains open
until supported cleanup, the full native journey, and durable receipt/readback
evidence pass.
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

Continue PR #192 in the existing worktree. Resume the dedicated isolated
Chrome profile if it still holds its normal authenticated session; otherwise
wait for normal user sign-in without requesting or copying credentials. Run the
exact authenticated `s3_ssl` native Reject journey, bounded live recovery
checks, and supported UI cleanup; never choose Approve. Then leave one
sanitized review handoff. Do not merge or start Issue #170 M4 follow-up work
until its acceptance gates are explicitly complete.

## Restart

`Read AGENTS.md, CONTEXT.md, Issue #191 and PR #192. Continue only the live s3_ssl Reject-only milestone; no Approve or AWS writes.`
