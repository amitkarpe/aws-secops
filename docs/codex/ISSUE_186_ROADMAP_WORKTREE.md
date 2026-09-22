# Codex roadmap worktree — Issue #186

Owning issue:
https://github.com/amitkarpe/aws-secops/issues/186

Parent roadmap:
https://github.com/amitkarpe/aws-secops/issues/170

## Worktree

Create a new worktree for:

`issue-186-exceptions-audit-ledger`

Keep this independent from Issue #176 / PR #177.

## Read first

1. `AGENTS.md`
2. `CONTEXT.md`
3. `SPEC.md`
4. Issue #186
5. Issue #170
6. PR #187
7. current `main`
8. M2 from #180/#181
9. M3A from #182/#183
10. M3B from #184/#185

## Objective

Implement M4A only:

`deterministic exception records -> exact resolution -> freeze integrity -> append-only audit ledger -> bounded operator/audit views`

Initial scope:
- synthetic/local
- restricted_ssh first
- no live AWS mutation
- no new controls
- reuse current finding, selection, freeze, decision and result primitives

## Hard boundaries

- no live AWS mutation
- no IAM/OIDC/networking
- no new controls
- no private CloudSCAPE/GovTech data
- no second approval engine
- no generic model execution tool
- no M4B control expansion
- exception != compliance
- expired/revoked exception cannot exclude
- audit evidence never authorizes execution
- keep independent from PR #177

## Milestones

1. strict durable exception schema + revisions
2. current-truth exception resolution
3. append-only structured event ledger
4. expiry/revoke/replay/failure invariants
5. compact operator/audit views + backend export

Run full regression and focused M4A acceptance.

Work autonomously.
Keep using PR #187.
Do not create micro-PRs.

Finish with:

`HANDOFF: CHATGPT`

Include changed files, tests, exception lifecycle proof, freeze-integrity proof, Reject/Approve/replay audit proof, export evidence, safety checks, and exact merge recommendation.
