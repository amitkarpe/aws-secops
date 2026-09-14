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

## Current authority

**Issue #36 — Establish ChatGPT-first GitHub OIDC + IaC deployment path**

https://github.com/amitkarpe/aws-secops/issues/36

## Current state

- Read-only GitHub OIDC preflight passed from `main`: https://github.com/amitkarpe/aws-secops/actions/runs/34818083174
- PR #42 merged the isolated deployment-canary role/workflow/IaC.
- PR #43 fixed the reserved SSM name; the canary now uses `/amitkarpe/aws-secops/deployment-canary`.
- PR #43 validation passed: 128 offline tests, Documentation Pages, both CloudFormation templates, and Access Analyzer with zero findings.
- The deploy-canary bootstrap role stack `aws-secops-github-oidc-deploy-canary` is `UPDATE_COMPLETE` with exact repo/main OIDC trust and exact canary stack/parameter scope.
- The deployment canary itself has not run yet; Demo v1 remains untouched.
- Issue #36 contains the current `HANDOFF: CODEX` for the final local `gh` variable setup + workflow dispatch.

## Current next action

1. X sets `AWS_SECOPS_DEPLOY_CANARY_ROLE_ARN` and `AWS_DEPLOY_CANARY_ENABLED=true` locally with `gh` (keep values out of public Git).
2. X runs `aws-deploy-canary.yml` from `main` using the authorized personal AWS context.
3. Verify the new workflow PASS and the SSM commit marker independently with AWS Core.
4. Confirm Demo v1 remained untouched.
5. Only after the canary passes, choose an existing Demo v1 component for explicit adoption/import design.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
