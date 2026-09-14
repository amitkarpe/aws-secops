# GitHub OIDC bootstrap — Issue #36

## Goal

Establish a repository-specific GitHub OIDC identity for `amitkarpe/aws-secops` without changing the existing Demo v1 runtime.

## Trust boundary

The bootstrap role trusts only the exact GitHub Actions subject for `main`:

`repo:amitkarpe/aws-secops:ref:refs/heads/main`

The expected audience is `sts.amazonaws.com`.

This repository must not reuse account IDs, role ARNs, Terraform state identities, or retained resource names from the reference repository `mytestlab123/chatgpt-aws`.

## Stage 1 scope

Stage 1 is intentionally read-only. It proves that GitHub Actions can obtain short-lived AWS credentials through OIDC and inspect the retained `aws-secops` lab state in `ap-southeast-1`.

It must not deploy, restart, replace, import, adopt, or mutate the existing Demo v1 runtime.

## Bootstrap boundary

The OIDC role itself cannot be created by assuming itself. One trusted operator action is therefore required to create the initial CloudFormation stack from `infra/github-oidc/template.yml`.

After the role exists, the repository can use the role for approved GitHub Actions workflows. Repository variables should hold non-secret deployment bindings such as the role ARN and expected account ID. No long-lived AWS access keys are required.

## Delivery model

```text
PR validation (no AWS credentials)
  -> merge to main
  -> manual workflow_dispatch
  -> GitHub OIDC short-lived role
  -> read-only preflight
  -> AWS Core independent verification
```

Any later expansion from read-only preflight to deployment permissions requires explicit review under Issue #36 and must preserve the existing human approval -> AgentCore Gateway/Policy -> exact remediation tool boundary.
