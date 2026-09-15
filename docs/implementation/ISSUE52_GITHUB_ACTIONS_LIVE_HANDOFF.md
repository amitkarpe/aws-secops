# Issue #52 — GitHub Actions live deployment handoff

Owner: Codex / X execution worker
Parent authority: Issue #49
Execution issue: Issue #52

## Goal

Complete the already-authorized GitHub-side live deployment step for the read-only `aws_secops_operator` Harness without bypassing the repository operating model.

> AWS Core discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS Core independently verifies.

## Current truth

- PR #50 is merged to `main`.
- Bootstrap stack `aws-secops-operator-harness-deploy-roles` is `CREATE_COMPLETE`.
- Dedicated GitHub OIDC deploy and CloudFormation execution roles exist and were independently verified.
- Exact repo + `main` trust remains required.
- The Harness application stack is not yet deployed.
- Demo v1 remains unchanged.
- GitHub Actions repository Variables/Secrets are persistent repository configuration; they are not tied to one PR or one workflow run.

## Long-term GitHub Actions configuration model

Use the smallest durable split below for this public repository.

### Repository Variables

Variables are non-secret operational configuration. They may be visible to workflows and are not a masking boundary.

- `AWS_REGION=ap-southeast-1`
- `AWS_OPERATOR_HARNESS_DEPLOY_ENABLED=true`

`AWS_OPERATOR_HARNESS_DEPLOY_ENABLED` is a persistent kill switch for this specific deployment path. Set it to `false` whenever live deployment should be disabled.

### Repository Secrets

Keep account/role identifiers out of normal public workflow output even though they are not AWS credentials:

- `AWS_ALLOWED_ACCOUNT_ID`
- `AWS_SECOPS_OPERATOR_HARNESS_DEPLOY_ROLE_ARN`
- `AWS_SECOPS_OPERATOR_HARNESS_STACK_EXECUTION_ROLE_ARN`

These values are reusable for future runs of this exact bounded Harness deployment workflow. They are not generic deployment authority for unrelated AWS work.

### Do not create

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN`
- a generic administrator role ARN for Actions
- generic `AWS_DEPLOY_ROLE_ARN` reused across unrelated workloads

GitHub OIDC remains the authentication mechanism. Future deployment workflows should receive their own narrowly scoped role secret rather than reusing this Harness role.

Keep security-boundary values code-reviewed rather than configurable where practical. In particular, do not move the exact stack name, repository/ref trust, allowed tools, Config controls, or model-accessible permissions into freely changeable repository variables merely for convenience.

If this repository later needs separate dev/test/prod approval boundaries, use GitHub Environments with environment-scoped secrets/variables and protection rules. Do not add that complexity for this single personal-lab path yet.

## X task

Use the authenticated local GitHub CLI / GitHub access available to X. Do not put variable/secret values, AWS account IDs, role ARNs, credentials, or session material into Git, Issue comments, PR comments, screenshots, or public logs.

1. Re-read `AGENTS.md`, `CONTEXT.md`, `SPEC.md`, Issue #49, Issue #52, this handoff, and `.github/workflows/aws-deploy-operator-harness.yml`.
2. Verify exact repository is `amitkarpe/aws-secops` and default branch is `main`.
3. Obtain the bootstrap CloudFormation outputs using the already-authorized local AWS identity. Do not publish the returned private identifiers.
4. Update `.github/workflows/aws-deploy-operator-harness.yml` in this existing PR so:
   - `AWS_REGION` comes from `vars.AWS_REGION` and is still explicitly checked to equal `ap-southeast-1` before mutation;
   - `AWS_OPERATOR_HARNESS_DEPLOY_ENABLED` remains a repository Variable gate;
   - `AWS_ALLOWED_ACCOUNT_ID`, `AWS_SECOPS_OPERATOR_HARNESS_DEPLOY_ROLE_ARN`, and `AWS_SECOPS_OPERATOR_HARNESS_STACK_EXECUTION_ROLE_ARN` are read from `secrets.*`, not `vars.*`;
   - exact repo, `main`, stack name, OIDC trust, and IAM boundaries remain unchanged.
5. Configure repository settings with authenticated `gh` or equivalent access:
   - Variables: `AWS_REGION`, `AWS_OPERATOR_HARNESS_DEPLOY_ENABLED`
   - Secrets: `AWS_ALLOWED_ACCOUNT_ID`, `AWS_SECOPS_OPERATOR_HARNESS_DEPLOY_ROLE_ARN`, `AWS_SECOPS_OPERATOR_HARNESS_STACK_EXECUTION_ROLE_ARN`
6. Verify only the configuration **names** exist. Do not print values.
7. Run repository validation/CI for the workflow change and keep corrections in this PR.
8. Merge is required before live dispatch because the deployment workflow is `main`-only. Do not dispatch from this PR branch.
9. After PR merge, dispatch workflow `AWS operator Harness deploy` from `main` only.
10. Watch the workflow to terminal state.
11. If it fails, diagnose and correct only inside the already-approved Issue #49 boundary. Do not broaden OIDC trust, IAM permissions, repository scope, branch scope, workflow triggers, or model-accessible AWS capability.
12. If deployment succeeds, stop further AWS mutation and return control to G / ChatGPT for independent AWS Core verification.

## Required public-safe evidence

Update Issue #52 and/or this PR with only:

- two GitHub Variable names configured: PASS/FAIL;
- three GitHub Secret names configured: PASS/FAIL;
- workflow run URL / run ID;
- workflow ref: `main`;
- workflow terminal status;
- Harness stack terminal status reported by the workflow;
- `Demo v1 mutation: NO`;
- `Independent AWS Core verification: REQUIRED`.

Never post the configuration values.

## Stop conditions

Return `BLOCKED` instead of bypassing if:

- GitHub auth cannot write repository Actions Variables/Secrets;
- GitHub auth cannot dispatch the workflow;
- AWS access cannot read the bootstrap outputs;
- repo/ref differs from `amitkarpe/aws-secops` + `main`;
- a proposed fix would widen IAM/OIDC/tool authority.

Do not deploy the Harness directly with an administrator AWS session as a substitute for the GitHub OIDC workflow.

## Acceptance

1. The workflow uses the long-term Variable/Secret split above.
2. Two Variables and three Secrets are configured without exposing values.
3. PR validation passes and the PR is merged before deployment.
4. `AWS operator Harness deploy` is dispatched from `main`.
5. Workflow reaches success and the exact Harness stack reaches a successful terminal state.
6. No Demo v1 mutation occurs.
7. X posts `HANDOFF: CHATGPT` with the public-safe evidence and requests independent AWS Core verification.
