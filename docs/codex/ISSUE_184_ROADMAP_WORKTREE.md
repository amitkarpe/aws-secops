# Codex roadmap worktree — Issue #184

Owning issue:
https://github.com/amitkarpe/aws-secops/issues/184

Parent roadmap:
https://github.com/amitkarpe/aws-secops/issues/170

## Worktree

Create a new worktree for:

`issue-184-grouped-manual-selection`

Keep this independent from Issue #176 / PR #177.

## Read first

1. `AGENTS.md`
2. `CONTEXT.md`
3. `SPEC.md`
4. Issue #184
5. Issue #170
6. PR #185
7. current `main`
8. M2 implementation from #180 / #181
9. M3A implementation from #182 / #183

## Objective

Implement M3B only:

`grouped findings -> manual exact selection -> preview -> freeze -> native approval -> synthetic/no-op execute -> per-row result/export`

Initial pilot:
- synthetic/local;
- `restricted_ssh` only;
- no live AWS mutation;
- reuse M2 query store;
- reuse M3A freeze/approval/result concepts;
- Reject must prove zero dispatch.

## Hard boundaries

- no live AWS mutation;
- no IAM/OIDC/networking;
- no new controls;
- no private CloudSCAPE/GovTech data;
- no second approval engine;
- no generic model-accessible execution tool;
- no Issue #170 M4 work;
- pagination/sort/group changes must never silently change selection;
- keep independent from PR #177.

## Milestones

1. grouped query + exact server-owned selection state;
2. backend re-resolution + deterministic preview/freeze;
3. pagination/sort/group invariants + filtered select-all exactness;
4. native Approve/Reject reuse + synthetic/no-op proof;
5. compact Config-style UX + deterministic result export.

Run full regression and focused M3B acceptance.

Work autonomously.
Keep using PR #185.
Do not create micro-PRs.

Finish with:

`HANDOFF: CHATGPT`

Include changed files, tests, selection invariants, Reject/Approve proof, export evidence, safety checks, and exact merge recommendation.
