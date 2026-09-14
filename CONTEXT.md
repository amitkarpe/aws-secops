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
- The deploy-canary bootstrap role stack `aws-secops-github-oidc-deploy-canary` is `CREATE_COMPLETE`.
- Live verification found the original SSM path `/aws-secops/deployment-canary` is reserved by AWS; the deployment canary was not run.
- Active correction changes only the canary parameter path to `/amitkarpe/aws-secops/deployment-canary` in IaC, IAM scope, workflow, tests, and docs.
- Demo v1 remains untouched.

## Current next action

1. Review/merge the canary SSM-path correction.
2. Update the existing deploy-canary bootstrap stack from corrected `main`.
3. Configure `AWS_SECOPS_DEPLOY_CANARY_ROLE_ARN` and `AWS_DEPLOY_CANARY_ENABLED=true` without committing values.
4. Run `AWS deployment canary` manually from `main`.
5. Verify the SSM commit marker independently with AWS Core and confirm Demo v1 remained untouched.
6. Only after the canary passes, choose an existing Demo v1 component for explicit adoption/import design.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
