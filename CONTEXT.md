# Agent Context

This file is compact **current-only** state for ChatGPT/coding-agent continuity.

Repository: `amitkarpe/aws-secops`

## Current product truth

- Demo v1 live acceptance remains recorded for the personal Singapore lab.
- Supported remediation families remain S3 Block Public Access and restricted SSH on retained owned demo resources.
- Approved execution remains human approval -> Gateway/Policy -> exact family tool -> provider readback.
- The model has no generic AWS mutation tool.
- The new `aws_secops_operator` Harness is read-only and does not change Demo v1 remediation authority.

## Current operating model

> **AWS Core discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS Core independently verifies.**

## Current authority

**Issue #49 — Deploy the read-only AgentCore Harness through bounded GitHub OIDC**

https://github.com/amitkarpe/aws-secops/issues/49

Parent: Issue #44 — Promote AgentCore Harness to the AWS SecOps operator path.

## Current state

- PR #45 merged the read-only operator-Harness package: one `aws_secops_operator`, Nova 2 Lite, two exact AWS Config read tools, Gateway + Policy ENFORCE + Lambda.
- The two controls remain `s3-bucket-level-public-access-prohibited` and `restricted-ssh`.
- The Harness has no write, shell, generic AWS, or arbitrary resource-selection tool.
- Explicit remediation requests still route to the existing governed human-approval/executor path; direct Harness mutation is not authorized.
- Active implementation branch: `issue-49-harness-oidc-deploy`.
- PR #50 adds the bounded deployment path: exact repo/main GitHub OIDC -> exact CloudFormation stack -> dedicated CloudFormation execution role -> declared Harness resources.
- PR #50 offline regression checks passed.
- Fresh pre-merge AWS verification in `ap-southeast-1` passed: STS identity verified, both CloudFormation templates validated, and IAM Access Analyzer returned zero findings for the GitHub deploy and CloudFormation execution identity policies.
- No Issue #49 AWS resource mutation or live Harness deployment has occurred yet.

## Current next action

Merge PR #50 after its refreshed CI passes. Live AWS work remains a separate authority boundary: bootstrap the deployment roles, configure the required GitHub variables, run the manual main-only deployment workflow, then independently verify Harness/Gateway/Policy/Lambda behavior and the negative write boundary.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
