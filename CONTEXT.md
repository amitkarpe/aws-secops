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

Issue #36 is complete. No Demo v1 adoption/mutation milestone is currently authorized.

## Current state

- Read-only GitHub OIDC preflight passed: https://github.com/amitkarpe/aws-secops/actions/runs/34818083174
- PR #42 established the isolated deployment-canary role/workflow/IaC.
- PR #43 corrected the reserved SSM path before first execution.
- Deploy-canary bootstrap role stack is `UPDATE_COMPLETE` with exact repo/main OIDC trust and corrected bounded SSM scope.
- End-to-end GitHub OIDC write canary passed from `main`: https://github.com/amitkarpe/aws-secops/actions/runs/34828258876
- Independent AWS readback confirms stack `aws-secops-deployment-canary` is `CREATE_COMPLETE`, contains exactly one `AWS::SSM::Parameter`, and `/amitkarpe/aws-secops/deployment-canary` equals the deployed `main` commit SHA.
- Demo v1 remains outside this canary boundary.

## Current next action

Create a new Issue before touching Demo v1. Choose exactly one existing Demo v1 component and design its explicit IaC adoption/import boundary first; do not silently import or mutate retained resources.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
