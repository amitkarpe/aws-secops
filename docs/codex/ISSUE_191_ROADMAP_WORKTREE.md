# Codex Roadmap Autopilot — Issue #191 / PR #192

Owning issue: https://github.com/amitkarpe/aws-secops/issues/191  
Parent roadmap: https://github.com/amitkarpe/aws-secops/issues/170  
Active PR: https://github.com/amitkarpe/aws-secops/pull/192

## Mission

Own this milestone end-to-end. Do not stop after one failed command, one missing
dependency, one browser problem, or one runtime mismatch.

Deliver one accepted real-LAB proof:

`live s3_ssl read -> exact prepare/freeze -> native Reject -> durable receipt -> zero dispatch -> zero AWS writes -> fresh provider readback unchanged -> public-safe evidence`

This is **Reject-only**. Live Approve/remediation is not authorized.

## Start from current truth

1. Read `AGENTS.md`, `CONTEXT.md`, `SPEC.md`.
2. Read Issue #191, Issue #170, PR #192 and its latest comments.
3. Read merged prerequisite Issue #193 / PR #194.
4. Read `docs/implementation/ISSUE193_NATIVE_DECISION_RECEIPT.md`.
5. Read this file.
6. Fetch current `main` and current PR #192 head before changing anything.
7. Reconcile repository truth; ignore stale chat assumptions.

Current known state:
- PR #194 merged to main at `b5e1797a3d5e899b95edcba1c0791b2acbc6b7af`.
- PR #192 branch is currently diverged from main and must be refreshed safely.
- Browser automation from WSL is already proven:
  `WSL -> Windows Chrome -> DevToolsActivePort -> Windows node.exe -> Playwright Core`.
- The native final-decision gap is already solved on main by #193/#194.
- Existing PR #192 code already contains live read + isolated Reject-only contract work.

## Operating mode

Work as the implementation owner, not as a command runner.

You may autonomously:
- rebase/merge current `main` into the PR #192 branch and resolve bounded conflicts;
- inspect/download exact LibreChat v0.8.8-rc1 source for research;
- inspect retained runtime source/config and compare it with the pinned upstream source;
- study prior working browser/runtime patterns in this repo and related public learning repos;
- create temporary local worktrees, test fixtures, scripts, and throwaway browser profiles;
- install temporary local test dependencies needed for validation;
- run repeated research/debug/fix/retest loops;
- refactor the PR #192 implementation when needed to integrate cleanly with #193;
- deploy the reviewed repo-owned read/prepare/decision changes to the retained personal-LAB runtime;
- run live personal-LAB read-only discovery;
- run authenticated Reject-only browser/API E2E;
- clean temporary application/browser/test state where safe;
- update docs/evidence/CONTEXT/ROADMAP after acceptance.

Do **not** ask Amit for repeated `go`.

Do **not** stop just because the first approach fails. Investigate alternatives,
read source, reproduce locally, fix the root cause, retest, and continue.

Stop only at a genuine safety/access/authority gate.

## Hard boundaries

- no automated Approve;
- no human Approve for `s3_ssl` in this milestone;
- no live `s3_ssl` remediation;
- no AWS resource mutation;
- no CodeBuild/Gateway/Lambda remediation dispatch for `s3_ssl`;
- no IAM/OIDC/networking expansion;
- no generic model-accessible AWS API/mutation tool;
- no new account registration;
- no company/office/PROD scope;
- no third governed control;
- no browser secret/cookie/token export;
- no copying Amit's normal Chrome profile;
- no public/private credential material in Git;
- verify exact LAB identity, Region and alias before live work.

## Big Milestone A — reconcile and integrate

Goal: make PR #192 a clean descendant of current main and reuse the merged #193
decision boundary rather than duplicating it.

Work:
- refresh PR #192 onto current main;
- resolve conflicts carefully;
- remove/supersede duplicate local decision logic when #193 now provides the canonical contract;
- preserve the live fixed-query `s3_ssl` evidence collector;
- preserve exact batch/scope/evidence binding;
- wire #191 trusted prepare/freeze registration into
  `NativeDecisionReceipts.register(...)`;
- expose only the exact reject-only native decision tool required for #191;
- keep existing BPA/SSH execution routes untouched;
- update instructions/schema so `s3_ssl` may reach prepare/native Reject while
  live execution remains unauthorized.

Acceptance:
- no duplicated approval engine;
- no path from `s3_ssl` to BPA/SSH/CodeBuild execution;
- exact-tool/scope/user/TTL binding;
- existing BPA/SSH tests unchanged;
- full local regression green.

## Big Milestone B — deep runtime research and deployment readiness

Goal: prove the retained runtime matches the reviewed source and can accept the
bounded patch safely.

Codex may perform deep R&D here.

Preferred path:
1. inspect retained LibreChat version/source;
2. compare exact `resume.js` digest with the reviewed v0.8.8-rc1 pin;
3. dry-run the repo-owned patch installer;
4. validate operator decision-receipt backend state/config;
5. validate the HMAC secret is present only in private runtime config;
6. validate receipt DB location/permissions/reopen behavior;
7. prepare an idempotent deployment + rollback procedure;
8. run targeted smoke tests before full E2E.

If the runtime source differs:
- download/read the exact installed/upstream source;
- explain the semantic delta;
- adapt the version pin only if the same post-validation/post-CAS/pre-resume
  transaction boundary is preserved;
- add tests for the new exact source;
- do not weaken the fail-closed contract merely to make the patch apply.

If deployment tooling is missing:
- build the smallest repo-owned idempotent deploy/check script in this same PR;
- do not create a new micro-PR.

Acceptance:
- exact deployed source/version known;
- patch install is deterministic/idempotent;
- source drift fails closed;
- rollback path exists;
- receipt failure cannot reach `resumeCompletion`;
- Approve remains blocked and non-dispatching by construction.

## Big Milestone C — authenticated real browser E2E

Goal: prove the actual native card/resume path from the real UI.

Use the already proven architecture:

`WSL Codex/Bash -> Windows chrome.exe -> dedicated debug profile -> DevToolsActivePort -> Windows node.exe -> Playwright Core -> localhost CDP`

Do not use Amit's normal profile.

Codex owns the complete troubleshooting loop:
- launch dedicated browser profile;
- let Amit authenticate only if human login is genuinely required;
- attach with Windows Node from WSL;
- inspect selectors/network/runtime state as needed;
- fix harness/product/runtime issues in-scope;
- retry until acceptance or a genuine stop gate.

Required journey:

1. verify LAB identity/Region/alias;
2. Status/read;
3. obtain one exact live `s3_ssl` finding;
4. prepare/freeze exact candidate;
5. verify batch/scope/provider evidence binding;
6. verify native approval card;
7. submit **REJECT**;
8. verify durable receipt = `REJECTED`;
9. verify downstream remediation/executor/CodeBuild/Gateway/Lambda dispatch = 0;
10. verify AWS writes = 0;
11. perform fresh provider readback;
12. prove provider state semantically unchanged;
13. verify audit chain prepare/freeze/Reject/readback;
14. clean disposable browser/test/conversation state where supported.

Do not test live Approve. The blocked-Approve path is already repository-tested
as a safety boundary.

## Big Milestone D — failure/recovery proof

Do not accept only the happy path.

Exercise bounded failure modes without AWS mutation:
- stale/mismatched batch/scope;
- duplicate/racing Reject submission;
- receipt endpoint unavailable;
- wrong HMAC;
- expired freeze;
- source drift / patch mismatch;
- browser reconnect/retry after a consumed decision;
- service restart/reopen with durable receipt intact.

Expected behavior:
- fail closed;
- no tool/remediation dispatch;
- no AWS write;
- no silent retry;
- no duplicate receipt;
- truthful UI/API error.

Fix routine defects discovered here in the same PR.

## Big Milestone E — acceptance, merge, and roadmap continuation

Persist public-safe evidence containing:
- exact PR head;
- exact main prerequisite SHA;
- tests/workflow IDs;
- runtime LibreChat version/source digest result;
- LAB identity verification result using aliases only in public evidence;
- provider evidence digest/version;
- batch/scope digest;
- native Reject decision receipt;
- zero downstream dispatch proof;
- zero AWS writes proof;
- post-Reject provider readback outcome;
- failure-mode validation summary;
- cleanup result;
- no automated/human Approve;
- any deferred exception-aware case and why.

Then:
1. run full repository validation;
2. make PR #192 review-ready;
3. post one final `HANDOFF: CHATGPT`;
4. recommend squash-merge only if acceptance is fully green;
5. after merge, update `CONTEXT.md` / roadmap current truth;
6. close Issue #191 only when the live native Reject proof is complete;
7. then select the next bounded milestone under Issue #170.

## Research options — choose autonomously

Use these in order when blocked:

### Option 1 — current repo/runtime first
Inspect current PR/main/runtime and fix the real integration directly.

### Option 2 — upstream/source deep dive
Clone/download LibreChat v0.8.8-rc1 or exact deployed source; trace the complete
HITL path, tests, resume controller, tool mapping and lifecycle behavior.

### Option 3 — historical known-good patterns
Mine:
- this repo's earlier LibreChat authenticated E2E work;
- `mytestlab123/agentic-ai-cybersecurity-lab`;
- `mytestlab123/AgentCore`;
- Agent OS Playwright/WSL guidance.

Use them to recover known-good browser/deployment patterns, not to copy stale
architecture blindly.

## Stop gates

Stop only if one of these is true:
- LAB account/Region/alias mismatch;
- implementation would require AWS resource mutation;
- implementation would require live/automated Approve;
- required fix needs new IAM/OIDC/network exposure;
- credentials/secrets would need to be exposed;
- company/PROD scope is required;
- a third control is required;
- the only remaining solution materially changes the approved architecture
  beyond #191/#193;
- required live access is unavailable and no useful repository/R&D work remains.

Routine test failures, source mismatches, browser errors, merge conflicts,
missing local dependencies, stale selectors, service restarts, and deploy-script
bugs are **not** stop gates.

## Final handoff

Only when a meaningful milestone is complete or a real stop gate exists, post:

`HANDOFF: CHATGPT`

Include:
- exact head;
- what changed;
- research performed;
- tests/workflows;
- runtime/deployment result;
- native Reject proof;
- zero dispatch / zero writes proof;
- provider readback result;
- cleanup result;
- unresolved risk/stop gate if any;
- exact merge recommendation.

Do substantial work before handing back. Avoid micro-handoffs.
