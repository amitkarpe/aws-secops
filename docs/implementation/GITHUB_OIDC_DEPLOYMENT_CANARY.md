# GitHub OIDC deployment canary — Issue #36

## Goal

Prove the first bounded GitHub OIDC **write** path without adopting or changing Demo v1.

```text
reviewed main
  -> manual workflow_dispatch
  -> repo/main-specific GitHub OIDC role
  -> CloudFormation stack
  -> one SSM parameter
  -> provider readback
```

## Boundary

This milestone manages only:

- CloudFormation stack `aws-secops-deployment-canary`;
- SSM parameter `/aws-secops/deployment-canary`.

The parameter value is the deployed Git commit SHA. Successful provider readback proves the reviewed `main` commit reached AWS through short-lived GitHub OIDC credentials.

It does **not** adopt, redeploy, restart, import, or mutate the existing S3/SSH remediation demo, Lambda functions, AgentCore Gateways/Policies, EC2, Security Groups, or retained demo resources.

## Deployment identity

`infra/github-oidc/deploy-canary-role.yml` defines a separate role:

`github-actions-aws-secops-deploy-canary`

Trust remains exact to the ID-qualified `amitkarpe/aws-secops` `main` subject and `sts.amazonaws.com` audience. The role is restricted to `ap-southeast-1`, the canary CloudFormation stack, and the canary SSM parameter.

The deployment role is deliberately separate from the read-only preflight role.

## One-time bootstrap

The deploy role cannot create itself. After this PR is reviewed and merged, one explicitly authorized trusted operator action is required to create the bootstrap role stack from:

`infra/github-oidc/deploy-canary-role.yml`

Then configure non-secret repository variables:

- `AWS_SECOPS_DEPLOY_CANARY_ROLE_ARN`
- `AWS_ALLOWED_ACCOUNT_ID` (already used by the preflight workflow)
- `AWS_DEPLOY_CANARY_ENABLED=true`

Do not commit their values.

## Live workflow

`.github/workflows/aws-deploy-canary.yml` is:

- `workflow_dispatch` only;
- `main` only;
- exact-repository-bound;
- explicitly enabled by repository variable;
- short-lived OIDC only;
- one isolated stack/parameter mutation;
- followed by direct SSM provider readback.

PR validation remains credential-free.

## Acceptance

The milestone is proven when the manual workflow succeeds on `main`, the SSM value equals that workflow's commit SHA, and independent AWS readback confirms no Demo v1 mutation.

Only after this canary succeeds should Issue #36 select an existing Demo v1 component for an explicit adoption/import design.
