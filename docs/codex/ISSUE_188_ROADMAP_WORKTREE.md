# Codex roadmap worktree — Issue #188

Owning issue:
https://github.com/amitkarpe/aws-secops/issues/188

Parent roadmap:
https://github.com/amitkarpe/aws-secops/issues/170

## Worktree

Create a new worktree for:

`issue-188-s3-ssl-governed-expansion`

Keep this independent from Issue #176 / PR #177.

## Read first

1. `AGENTS.md`
2. `CONTEXT.md`
3. `SPEC.md`
4. Issue #188
5. Issue #170
6. PR #189
7. current `main`
8. M1 capability adapter from #178/#179
9. M2 query/export from #180/#181
10. M3A/M3B from #182/#183 and #184/#185
11. M4A from #186/#187

## Objective

Implement M4B only:

`existing restricted_ssh governed path + shared M4A exception/audit substrate -> add s3_ssl as the second synthetic governed control`

## Hard boundaries

- synthetic/local only;
- no live AWS mutation;
- no IAM/OIDC/networking;
- no private CloudSCAPE/GovTech mappings;
- no generic remediation engine;
- no second approval/exception/audit engine;
- no third control;
- mixed-control scope must fail closed;
- capability metadata never authorizes execution by itself;
- keep independent from PR #177.

## Milestones

1. explicit public-safe s3_ssl governed capability;
2. deterministic synthetic S3 evidence;
3. reuse selection/freeze/exception/audit pipeline;
4. cross-control isolation + mixed-scope fail-closed proof;
5. compact two-control operator proof.

Run full regression and focused M4B acceptance.

Work autonomously.
Keep using PR #189.
Do not create micro-PRs.

Finish with:

`HANDOFF: CHATGPT`

Include changed files, tests, cross-control isolation evidence, exception-binding proof, Reject/Approve proof, audit/export evidence, safety checks, and exact merge recommendation.
