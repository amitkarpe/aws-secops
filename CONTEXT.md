# Agent Context

This file is compact **current-only** state for ChatGPT/coding-agent continuity.

Repository: `amitkarpe/aws-secops`

## Current product truth

- Demo v1 live acceptance remains recorded for the personal Singapore lab.
- Supported families remain S3 Block Public Access and restricted SSH on retained owned demo resources.
- Approved execution remains human approval -> Gateway/Policy -> exact family tool -> provider readback.
- The model has no generic AWS mutation tool.

## Current operating model

> **AWS Core discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS Core independently verifies.**

`AGENTS.md` is the short-session router. It loads `PROMPT.md` automatically. Codex is optional.

## Current authority

**Issue #36 — Establish ChatGPT-first GitHub OIDC + IaC deployment path**

https://github.com/amitkarpe/aws-secops/issues/36

## Current state

- PR #37 established the repo-specific read-only GitHub OIDC preflight path.
- PR #41 corrected trust to the exact ID-qualified GitHub `main` subject observed in CloudTrail and added the local/Codex operator helper.
- End-to-end `AWS OIDC preflight` passed from `main`:
  https://github.com/amitkarpe/aws-secops/actions/runs/34818083174
- The preflight role remains read-only and Singapore-only for Config, Lambda, and AgentCore inspection.
- PR validation remains credential-free.
- Existing Demo v1 runtime has not been adopted or redeployed through Issue #36.

## Current next action

1. Choose the first existing AWS component that should become repo-owned IaC.
2. Design the smallest separate deployment role/workflow for that exact target.
3. Keep PR validation credential-free and live deployment `main`-only/manual.
4. Do not silently import/adopt or mutate Demo v1 before that boundary is reviewed.
5. Verify any later live change independently with AWS Core.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
