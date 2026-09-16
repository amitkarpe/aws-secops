# Agent Context

Updated: 2026-09-17
Status: current-only restart state
Repository: `amitkarpe/aws-secops`

> Keep detailed completed acceptance evidence in Git history, closed Issues/PRs, and existing evidence/docs. This file routes current work.

## Current Product Truth

- Demo v1 remains the accepted personal Singapore lab baseline.
- Supported remediation families remain S3 Block Public Access and restricted SSH on retained owned demo resources.
- Governed execution remains human approval -> Gateway/Policy -> exact family tool -> provider readback.
- The model has no generic AWS mutation tool.
- `aws_secops_operator` remains the read-only AgentCore Harness reasoning/investigation layer.
- Explicit `fix/apply/execute` requests do not mutate through the Harness; mutation remains on the separate governed human-approval path.
- Issue #60 and Issue #70 are complete. Their implementation and acceptance detail is historical proof, not restart-state authority.

## Operating Model

> **AWS Core discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS Core independently verifies.**

GitHub is durable engineering state. AWS is runtime state. ChatGPT Web is the default controller; Codex is optional for deeper implementation or independent validation.

A repository write never authorizes AWS mutation. If a connector cannot start a manual workflow, do not widen its trigger merely to bypass the connector; use only the explicitly authorized documented fallback.

## Current Authority

### Issue #68 — two-account read-only SecOps proof

https://github.com/amitkarpe/aws-secops/issues/68

Status: **BLOCKED / deferred prerequisite**.

Start it only when a second explicitly authorized owned AWS read scope already exists. Do not create cross-account access merely to make the milestone pass. The first proof remains read-only; cross-account mutation is a separate later security decision.

## Current Safety Boundary

- Preserve human approval and exact bounded mutation tools.
- No generic model-accessible AWS mutation capability.
- No new cross-account role/trust merely for Issue #68.
- No widening IAM/OIDC/Gateway/Policy authority without the owning Issue/SPEC and required review.
- Re-verify AWS identity, Region and current provider state before any AWS-specific action.
- Config-only CLEAR or historical acceptance must not be presented as current provider-state proof.

## Continuation

For a known objective:

1. use the named Issue/PR as the execution packet;
2. read its latest relevant authorized comment/handoff when there is a new delta;
3. fetch current HEAD and fresh provider state only as required by the task;
4. continue within the existing Issue/SPEC authority.

Reload `AGENTS.md`, this file, `PROMPT.md`, `SPEC.md`, or wider repository context only for cold start, materially changed governing files, ambiguous identity/objective, stale/incomplete/contradictory state, or a new authority/safety domain.

## Next Action

1. Do not implement Issue #68 until its second-account prerequisite exists.
2. If that prerequisite appears, design the smallest exact two-account read-only proof in Git/IaC first and independently verify account-distinguished evidence and zero mutation.
3. If new unblocked product work is desired before then, create a separate standalone Issue from `ROADMAP.md`; do not mix it into Issue #68.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future scope use `ROADMAP.md`.
