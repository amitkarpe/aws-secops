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

Current implementation PR:

**PR #37 — bootstrap repo-specific GitHub OIDC identity**

https://github.com/amitkarpe/aws-secops/pull/37

This is the active engineering milestone unless repository state has moved.

Fresh-session command:

> `Using GitHub app - Read AGENTS.md, CONTEXT.md, active Issue/PR and continue.`

A session receiving that instruction should read `AGENTS.md`, this file, `PROMPT.md`, Issue #36, and any active PR linked to it; verify current GitHub state; verify current AWS identity and Region with AWS Core; then continue from repository state without asking Amit to repeat project history.

## Current state

- PR #37 defines a repository-specific GitHub OIDC preflight role and a manual, `main`-only preflight workflow.
- Trust is bound to `repo:amitkarpe/aws-secops:ref:refs/heads/main` with audience `sts.amazonaws.com`.
- The preflight role is read-only and constrained to `ap-southeast-1` for Config, Lambda, and AgentCore inspection.
- PR validation remains credential-free.
- CloudFormation template validation passed in `ap-southeast-1` with `CAPABILITY_NAMED_IAM` required.
- AWS Access Analyzer returned zero findings for the inline preflight policy.
- The account-level GitHub OIDC provider exists with client ID `sts.amazonaws.com`.
- Existing Demo v1 resources have not been adopted, redeployed, or mutated by Issue #36 work.

## Current next action

1. Complete review and merge PR #37 after green CI.
2. Perform the one-time OIDC role bootstrap only with explicit authorization.
3. Configure the repository variables required by `.github/workflows/aws-oidc-preflight.yml`.
4. Run the manual preflight workflow from `main`.
5. Verify the assumed identity and retained AWS state independently with AWS Core.
6. Only after successful preflight, design the next explicitly reviewed deployment/adoption boundary; do not silently import or mutate Demo v1.
7. Keep reusable learning under `docs/` and keep this file current-only.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
