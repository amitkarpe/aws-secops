# Agent Context

This file is compact **current-only** state for ChatGPT/coding-agent continuity.

Repository: `amitkarpe/aws-secops`

## Current product truth

- Demo v1 live acceptance is recorded for the personal Singapore lab.
- Supported families remain S3 Block Public Access and restricted SSH on retained owned demo resources.
- Current primary agent path is LibreChat + native Bedrock Nova 2 Lite + bounded MCP tools.
- S3 and SG retain separate native human approvals.
- Approved execution remains Gateway -> Policy -> exact family tool -> provider readback.
- The model has no generic AWS mutation tool.
- Provider readback is immediate remediation truth; Config is independent asynchronous evidence.
- PR #33 reliability hardening is merged on `main`; that source change is not by itself proof that the live demo host was redeployed.

## Current operating model

ChatGPT is the primary controller/operator.

> **AWS Core discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS Core independently verifies.**

`AGENTS.md` is the short-session router. It loads `PROMPT.md` automatically. Codex is optional.

## Current authority

**Issue #36 — Establish ChatGPT-first GitHub OIDC + IaC deployment path**

https://github.com/amitkarpe/aws-secops/issues/36

This is the active engineering milestone unless repository state has moved.

Fresh-session command:

> `Using GitHub app - Read AGENTS.md, CONTEXT.md, active Issue/PR and continue.`

A session receiving that instruction should read `AGENTS.md`, this file, `PROMPT.md`, Issue #36, and any active PR linked to it; verify current GitHub state; verify current AWS identity and Region with AWS Core; then continue from repository state without asking Amit to repeat project history.

## Current next action

1. Verify GitHub and AWS identity/state.
2. Audit existing deployment scripts/workflows/IaC and retained AWS resources.
3. Reuse the OIDC/control-path pattern from `mytestlab123/chatgpt-aws` without copying identities.
4. Design repo-specific GitHub OIDC trust and the smallest practical deployment role.
5. Implement repository-owned IaC plus a main-only/manual deployment workflow through a PR.
6. Keep PR validation AWS-free where practical.
7. Deploy only after explicit authorization.
8. Verify resulting AWS state independently with AWS Core.
9. Record reusable learning in `docs/`.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
