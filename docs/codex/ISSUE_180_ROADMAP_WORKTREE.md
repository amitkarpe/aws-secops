# Codex roadmap worktree — Issue #180

Owning issue:
https://github.com/amitkarpe/aws-secops/issues/180

Parent roadmap:
https://github.com/amitkarpe/aws-secops/issues/170

## Worktree

Create a new worktree for:

`issue-180-1k-query-export`

Keep this independent from Issue #176 / PR #177.

## Read first

1. `AGENTS.md`
2. `CONTEXT.md`
3. `SPEC.md`
4. Issue #180
5. Issue #170
6. PR #181
7. current main
8. CloudSCAPE `fixtures/1k-fixture-spec.json`

## Objective

Implement Issue #170 M2:

`deterministic 1K backend truth -> server-side summary/filter/sort/search/page -> bounded model page -> CSV export`

## Hard boundaries

- synthetic/local first;
- no AWS mutation;
- no IAM/OIDC/network changes;
- no bulk remediation;
- no native approval/executor changes;
- no private CloudSCAPE/GovTech data;
- no full 1K payload in model context;
- max page size 100;
- keep Issue #178 capability ceilings unchanged;
- keep independent from PR #177.

## Milestones

1. deterministic 1K fixture/generator;
2. bounded query/filter/sort/search/page layer;
3. CSV export from backend truth;
4. Compliance Agent read-only integration + 1K acceptance.

Run full regression.
Measure representative query/export timings.
Do not invent performance budgets before evidence.

Work autonomously.
Keep using PR #181.
Do not create micro-PRs.

Finish with:

`HANDOFF: CHATGPT`

Include changed files, tests, 1K acceptance evidence, performance observations, safety checks, and exact merge recommendation.
