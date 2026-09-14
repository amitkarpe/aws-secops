# Agent Context

This file is compact current state for ChatGPT/coding-agent continuity. Human readers should use `README.md`, `PROJECT_STATUS.md`, `SPEC.md` and the MkDocs site.

Repository: `amitkarpe/aws-secops`

## Current product truth

- Demo v1 live acceptance is recorded for the personal Singapore lab; no company or production resources.
- Supported families remain exactly:
  - S3 bucket-level Block Public Access on the retained owned demo fleet;
  - restricted SSH on retained owned unattached Security Groups.
- Current primary agent path is LibreChat + native Bedrock Nova 2 Lite + bounded MCP tools. Historical Harness experiments are not the current primary architecture.
- S3 and SG retain separate native human approvals.
- Approved execution remains Gateway -> Policy -> exact family tool -> provider readback.
- The model has no generic AWS mutation tool and cannot select arbitrary execution targets.
- Current planners require complete retained-family readiness; no arbitrary-subset claim.
- Provider readback is immediate remediation truth; Config is independent asynchronous evidence.
- Operator Prepare demo is separate operator maintenance and is never an agent reset capability.
- PR #33 reliability hardening is merged on `main`: bounded Config reads, non-replay interruption handling for S3/SG, stronger saved verification evidence, and offline regression CI.
- Those PR #33 code changes are not automatically proof that the existing live AWS demo host has been redeployed with the new runtime.

## Current operating model

ChatGPT is now the primary controller/operator for this repository.

> **AWS Core discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS Core independently verifies.**

`PROMPT.md` contains the full operating model. `AGENTS.md` is the short-session router and must automatically route a fresh session to `PROMPT.md`; Amit does not need to paste the bootstrap URL.

Codex is optional, not a required dependency.

## Current authority

- **Issue #34 / PR #35** finalize the documentation/bootstrap change that makes the short ChatGPT session command durable in the repository.
- **Issue #36** is the next active engineering milestone: establish repo-specific GitHub OIDC + repository-owned IaC/deployment workflow, then verify resulting AWS state with AWS Core.

After PR #35 is merged, Issue #36 becomes the primary active authority for the next chat session unless repository state has moved.

Fresh-session command:

> `Using GitHub app - Read AGENTS.md, CONTEXT.md, active Issue/PR and continue.`

A session receiving that instruction should read `PROMPT.md` automatically, verify current GitHub state, read the active Issue/PR, and continue without asking Amit to restate repository context.

## Current publication rule

The repository and site are public. Keep credentials, private infrastructure identifiers, auth/session material, raw private findings and private screenshots out of Git, Issues/PRs, Actions artifacts/logs and public documentation.

## Current safety boundary

The bootstrap/documentation work does not itself authorize AWS resource creation, deployment, restart, reset/re-arm, remediation, IAM/Policy mutation or live-journal edits.

For Issue #36, verify current GitHub and AWS identity/state first. Prefer read-only discovery, then define durable AWS state in Git/IaC. Deployment requires explicit authorization and must be independently verified afterward with AWS Core.

For public status and known limitations use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
