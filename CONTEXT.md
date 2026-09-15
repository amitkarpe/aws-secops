# Agent Context

This file is compact **current-only** state for ChatGPT/coding-agent continuity.

Repository: `amitkarpe/aws-secops`

## Current product truth

- Demo v1 live acceptance remains recorded for the personal Singapore lab.
- Supported remediation families remain S3 Block Public Access and restricted SSH on retained owned demo resources.
- Approved execution remains human approval -> Gateway/Policy -> exact family tool -> provider readback.
- The model has no generic AWS mutation tool.
- The `aws_secops_operator` Harness is read-only and does not change Demo v1 remediation authority.

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
- PR #50 merged the bounded deployment path: exact repo/main GitHub OIDC -> exact CloudFormation stack -> dedicated CloudFormation execution role -> declared Harness resources.
- PR #53 merged the durable GitHub Actions configuration model: `AWS_REGION` and the deploy enable flag as repository Variables; account/role identifiers as repository Secrets; no static AWS access keys.
- The live bootstrap stack `aws-secops-operator-harness-deploy-roles` is `CREATE_COMPLETE`.
- Main-only workflow run `34927383714` succeeded from `main` using GitHub OIDC. Caller/account and Region checks passed, the template validated, the exact Harness stack applied, and CloudFormation readback confirmed the expected `HarnessArn`, `GatewayArn`, `PolicyEngineId`, and `ReadFunctionArn` outputs.
- The Harness application stack `aws-secops-operator-harness` reached `CREATE_COMPLETE`.
- Demo v1 mutation during the Harness deployment: **NO**.
- Independent live functional verification of Harness/Gateway/Policy/Lambda behavior and the negative write boundary is still required before Issue #49 closes.

## Current next action

Perform independent read-only AWS verification for Issue #49: confirm Harness/runtime, Gateway, Policy ENFORCE / ACTIVE policy, Lambda read path, both exact Config controls, and the negative `fix/apply/execute` boundary. If that passes, record public-safe evidence, close Issue #49, and then decide whether parent Issue #44 is fully accepted.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
