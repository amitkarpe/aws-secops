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

- PR #37 established the repo-specific read-only GitHub OIDC preflight path.
- PR #41 corrected trust to the exact ID-qualified GitHub `main` subject.
- End-to-end read-only OIDC preflight passed from `main`:
  https://github.com/amitkarpe/aws-secops/actions/runs/34818083174
- PR #42 is merged and defines the first bounded OIDC write path: a separate deploy-canary role, one CloudFormation-managed SSM parameter, a manual `main`-only workflow, safety tests, and docs.
- The canary target is isolated from Demo v1: stack `aws-secops-deployment-canary`, parameter `/aws-secops/deployment-canary`.
- PR #42 validation passed: 128 offline tests, Documentation Pages, both CloudFormation templates, Access Analyzer with zero inline-policy findings, and exact-target IAM simulation.
- No deployment-canary AWS mutation has occurred yet.

## Current next action

1. With explicit live authorization, bootstrap the separate deploy-canary OIDC role.
2. Configure `AWS_SECOPS_DEPLOY_CANARY_ROLE_ARN` and `AWS_DEPLOY_CANARY_ENABLED=true` without committing values.
3. Manually run `AWS deployment canary` from `main`.
4. Verify the SSM commit marker independently with AWS Core and confirm Demo v1 remained untouched.
5. Only after the canary passes, choose an existing Demo v1 component for explicit adoption/import design.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
