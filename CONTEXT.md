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

Current implementation:

**PR #42 — prove bounded OIDC deployment with isolated canary**

https://github.com/amitkarpe/aws-secops/pull/42

## Current state

- PR #37 established the repo-specific read-only GitHub OIDC preflight path.
- PR #41 corrected trust to the exact ID-qualified GitHub `main` subject.
- End-to-end read-only OIDC preflight passed from `main`:
  https://github.com/amitkarpe/aws-secops/actions/runs/34818083174
- PR #42 adds a separate deploy-canary OIDC role, one CloudFormation-managed SSM parameter, a manual `main`-only workflow, safety tests, and docs.
- The canary target is intentionally isolated from Demo v1: stack `aws-secops-deployment-canary`, parameter `/aws-secops/deployment-canary`.
- Both new CloudFormation templates validate and the deploy-role inline policy has zero AWS Access Analyzer findings.
- No PR #42 AWS mutation has occurred; PR validation remains credential-free.

## Current next action

1. Finish review/CI for PR #42.
2. Merge only when eligible.
3. With explicit live authorization, bootstrap the separate deploy-canary role.
4. Configure the required non-secret repository variables and manually run the canary workflow from `main`.
5. Verify the SSM marker independently with AWS Core and confirm Demo v1 remained untouched.
6. Only after the canary passes, choose an existing Demo v1 component for explicit adoption/import design.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
