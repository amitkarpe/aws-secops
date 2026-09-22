# Codex Roadmap Autopilot — Issue #191

Owning issue:
https://github.com/amitkarpe/aws-secops/issues/191

Parent roadmap:
https://github.com/amitkarpe/aws-secops/issues/170

## Worktree

Create a new worktree for:

`issue-191-s3-ssl-live-reject`

## Read first

1. `AGENTS.md`
2. `CONTEXT.md`
3. `SPEC.md`
4. Issue #191
5. Issue #170
6. PR #192
7. current `main`
8. M4B from #188/#189
9. PR #177 / Issue #176 if live read-evidence wiring depends on it
10. existing authenticated LibreChat/API Reject-only E2E harness

## Objective

Prove one real-LAB s3_ssl path:

`live read -> exact prepare -> native Reject -> zero remediation dispatch -> zero AWS writes -> fresh provider readback unchanged -> durable audit evidence`

Reject-only.

## Hard boundaries

- no automated Approve;
- no live remediation;
- no AWS resource mutation;
- no IAM/OIDC/networking expansion;
- no generic AWS API/model tool;
- no new account registration;
- no company/office/PROD;
- no third control;
- verify exact LAB identity/Region/alias before live work;
- public-safe evidence only.

## Milestones

1. live s3_ssl fixed-query evidence wiring;
2. exact live prepare/freeze contract;
3. authenticated native Reject E2E;
4. exception-aware Reject proof if safely available without AWS mutation;
5. durable acceptance packet + restart truth.

If PR #177 is a dependency:
- refresh/rebase it on current main;
- preserve default-off read-only semantics;
- rerun exact-head checks;
- merge only if scope remains bounded.

Use the existing E2E harness. Do not create a second one.

Work autonomously.
Keep using PR #192.
Do not create micro-PRs.

Finish with:

`HANDOFF: CHATGPT`

Include:
- exact git head;
- tests/workflow IDs;
- LAB identity verification result;
- provider evidence digest;
- batch/scope evidence;
- native Reject proof;
- zero remediation dispatch;
- zero AWS writes;
- post-Reject provider readback;
- cleanup result;
- any real stop gate;
- exact merge recommendation.
