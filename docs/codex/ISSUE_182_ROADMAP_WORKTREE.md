# Codex roadmap worktree — Issue #182

Owning issue:
https://github.com/amitkarpe/aws-secops/issues/182

Parent roadmap:
https://github.com/amitkarpe/aws-secops/issues/170

## Worktree

Create a new worktree for:

`issue-182-csv-bulk-pilot`

Keep this independent from Issue #176 / PR #177.

## Read first

1. `AGENTS.md`
2. `CONTEXT.md`
3. `SPEC.md`
4. Issue #182
5. Issue #170
6. PR #183
7. current main
8. M2 code from Issue #180 / PR #181

## Objective

Implement M3A only:

`CSV candidate scope -> backend re-resolve -> preview -> freeze -> native approval -> bounded synthetic execute -> per-row result/export`

Initial pilot:
- synthetic/local;
- restricted_ssh only;
- no live AWS mutation;
- fake/no-op executor for Approve acceptance;
- Reject must prove zero dispatch.

## Hard boundaries

- CSV is never evidence or mutation authority;
- no live AWS mutation;
- no IAM/OIDC/networking;
- no generic execution tool exposed to model;
- no new approval system;
- no Config-GUI M3B work;
- no new controls;
- no private CloudSCAPE/GovTech data;
- reuse M2 query/export primitives;
- keep independent from PR #177.

## Milestones

1. strict CSV intake + deterministic normalization;
2. backend re-resolution + classified preview;
3. frozen batch + native approval contract;
4. fake/no-op Approve + Reject proof;
5. compact result UX + deterministic result export.

Run full regression and focused M3A acceptance.

Work autonomously.
Keep using PR #183.
Do not create micro-PRs.

Finish with:

`HANDOFF: CHATGPT`

Include changed files, tests, candidate/rejection/freeze evidence, Reject/Approve proof, export evidence, safety checks, and exact merge recommendation.
