# Codex worktree — Issue #176

This branch is the isolated Codex lane for:

**Persistent read-only AWS MCP evidence adapter**

Owning issue:

https://github.com/amitkarpe/aws-secops/issues/176

## Worktree

Create a separate worktree for branch:

`issue-176-persistent-mcp-evidence`

Do not reuse the completed v1 release worktree.

## Read first

1. `AGENTS.md`
2. `CONTEXT.md`
3. `SPEC.md`
4. Issue #176
5. Issue #130
6. PR #177
7. current main

## Objective

Implement one bounded, read-only SecOps evidence-provider boundary for persistent AWS MCP.

Target evidence families:

- AWS Config;
- S3 posture;
- Security Group exposure;
- one Inspector / CloudTrail / IAM-style query.

## Rules

- no AWS mutation;
- no new IAM/OIDC/networking;
- no generic arbitrary AWS API passthrough to the model;
- no credentials/tokens/session material;
- preserve current Compliance Agent v1 behavior;
- live enablement remains disabled by default;
- use fixtures/mocks if live MCP is unavailable;
- personal-LAB read-only access is acceptable only after identity verification;
- do not modify release tag/workflow/history;
- do not start Issue #170 M1 catalog work;
- avoid editing `CONTEXT.md` / `ROADMAP.md` unless final integration state truly requires it.

## Milestones

1. map current evidence architecture + schema;
2. implement normalized read-only provider boundary;
3. add representative Config/S3/SG/security evidence tests;
4. document integration/fallback gate and disabled-by-default hook if appropriate.

Work autonomously until acceptance or a real stop gate.

Prefer updating this same PR rather than creating micro-PRs.

Finish with:

`HANDOFF: CHATGPT`

Include:
- changed files;
- tests;
- live read evidence if any;
- remaining blockers;
- exact merge recommendation.
