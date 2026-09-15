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
- PR #50 merged the bounded deployment path: exact repo/main GitHub OIDC -> exact CloudFormation stack -> dedicated CloudFormation execution role -> declared Harness resources.
- Fresh pre-merge AWS verification in `ap-southeast-1` passed: STS identity verified, both CloudFormation templates validated, and IAM Access Analyzer returned zero findings for the GitHub deploy and CloudFormation execution identity policies.
- The live bootstrap stack `aws-secops-operator-harness-deploy-roles` reached `CREATE_COMPLETE`.
- Readback verified the exact repo+main OIDC trust, exact Harness stack boundary, exact CloudFormation execution-role pass, and service-constrained runtime role passes.
- The Harness application stack `aws-secops-operator-harness` has not been deployed yet, and Demo v1 has not been mutated.
- Current blocker is connector capability only: this ChatGPT GitHub interface does not expose repository Actions-variable writes or `workflow_dispatch`.

## Current next action

Configure the required repository Actions variables from the bootstrap stack outputs, manually run `AWS operator Harness deploy` from `main`, then independently verify Harness/Gateway/Policy/Lambda behavior and the negative write boundary with AWS Core. Do not bypass the approved GitHub OIDC apply path with direct AWS Core deployment.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
