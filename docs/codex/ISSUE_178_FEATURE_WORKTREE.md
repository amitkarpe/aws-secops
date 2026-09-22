# Codex feature worktree — Issue #178

Owning issue:
https://github.com/amitkarpe/aws-secops/issues/178

Parent roadmap:
https://github.com/amitkarpe/aws-secops/issues/170

Private reference contract:
`amitkarpe/cloudscape-remediation/integration/secops-contract.json`

## Worktree

Create a separate worktree for:

`issue-178-sanitized-capability-adapter`

Keep this independent from Issue #176 / PR #177.

## Read first

1. `AGENTS.md`
2. `CONTEXT.md`
3. `SPEC.md`
4. Issue #178
5. Issue #170
6. Issue #164
7. PR #179
8. CloudSCAPE `integration/secops-contract.json`

## Objective

Implement the sanitized private capability adapter for Issue #170 M1.

Public-safe generic controls only:

- s3_ssl
- s3_logging
- s3_backup
- restricted_ssh

Capability states:

`DETECT / EXPLAIN / PREPARE / REMEDIATE / VERIFY`

## Rules

- no private CloudSCAPE/GovTech mappings in this repo;
- no raw findings/account inventory;
- unknown controls stay unsupported/read-only;
- no model-invented remediation capability;
- approval remains independent from automability;
- no new AWS mutation path;
- no new IAM/OIDC/network changes;
- no Issue #170 M2 1K work;
- avoid touching Issue #176 files unless a tiny shared interface is unavoidable.

## Milestones

1. schema + public-safe model;
2. deterministic adapter + validation;
3. bounded Compliance Agent integration;
4. regression + first capability product proof.

Work autonomously.
Keep using PR #179.
Do not create micro-PRs.

Finish with:

`HANDOFF: CHATGPT`

Include changed files, tests, privacy/safety checks, and merge recommendation.
