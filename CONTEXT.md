# Agent Context

This file is compact **current-only** state for ChatGPT/coding-agent continuity.

Repository: `amitkarpe/aws-secops`

## Current product truth

- Demo v1 live acceptance remains recorded for the personal Singapore lab.
- Supported remediation families remain S3 Block Public Access and restricted SSH on retained owned demo resources.
- Approved execution remains human approval -> Gateway/Policy -> exact family tool -> provider readback.
- The model has no generic AWS mutation tool.

## Current operating model

> **AWS Core discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS Core independently verifies.**

## Current authority

**Issue #44 — Promote AgentCore Harness to the AWS SecOps operator path**

https://github.com/amitkarpe/aws-secops/issues/44

## Current state

- GitHub OIDC read-only preflight and bounded write canary both passed from `main`.
- Issue #44 promotes the proven `mytestlab123/lab1_agent` operator-Harness pattern into the real AWS SecOps repository without copying lab identities/resources.
- Active implementation branch: `issue-44-agentcore-harness-operator`.
- The first real Harness slice is one `aws_secops_operator` using Nova 2 Lite plus two exact AWS Config read tools through Gateway + Policy ENFORCE + Lambda.
- The two controls remain `s3-bucket-level-public-access-prohibited` and `restricted-ssh`.
- The Harness has no write, shell, generic AWS, or arbitrary resource-selection tool.
- Explicit remediation requests still route to the existing governed human-approval/executor path; direct Harness mutation is not authorized.
- No Issue #44 AWS deployment or Demo v1 mutation has occurred yet.

## Current next action

Finish PR validation for the Issue #44 Harness operator package. After review/merge, choose a bounded OIDC deployment path and independently verify live Harness/Gateway/Policy behavior before changing the trusted product contract.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
