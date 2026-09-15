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

## X task

Use the authenticated local GitHub CLI / GitHub access available to X. Do not put variable values, AWS account IDs, role ARNs, credentials, or session material into Git, Issue comments, PR comments, screenshots, or public logs.

1. Re-read `AGENTS.md`, `CONTEXT.md`, `SPEC.md`, Issue #49, Issue #52, this handoff, and `.github/workflows/aws-deploy-operator-harness.yml` on `main`.
2. Verify exact repository is `amitkarpe/aws-secops` and default branch is `main`.
3. Obtain the bootstrap CloudFormation outputs using the already-authorized local AWS identity. Do not publish the returned private identifiers.
4. Set these GitHub Actions repository variables with authenticated `gh variable set` or equivalent GitHub access:
   - `AWS_ALLOWED_ACCOUNT_ID`
   - `AWS_SECOPS_OPERATOR_HARNESS_DEPLOY_ROLE_ARN`
   - `AWS_SECOPS_OPERATOR_HARNESS_STACK_EXECUTION_ROLE_ARN`
   - `AWS_OPERATOR_HARNESS_DEPLOY_ENABLED=true`
5. Verify variable **names** exist without printing their values.
6. Dispatch workflow `AWS operator Harness deploy` from `main` only.
7. Watch the workflow to terminal state.
8. If it fails, diagnose and correct only inside the already-approved Issue #49 boundary. Do not broaden OIDC trust, IAM permissions, repository scope, branch scope, workflow triggers, or model-accessible AWS capability.
9. If deployment succeeds, stop further AWS mutation and return control to G / ChatGPT for independent AWS Core verification.

## Required public-safe evidence

Update Issue #52 and/or this PR with only:

- four GitHub variable **names** configured: PASS/FAIL;
- workflow run URL / run ID;
- workflow ref: `main`;
- workflow terminal status;
- Harness stack terminal status reported by the workflow;
- `Demo v1 mutation: NO`;
- `Independent AWS Core verification: REQUIRED`.

Never post the variable values.

## Stop conditions

Return `BLOCKED` instead of bypassing if:

- GitHub auth cannot write repository Actions variables;
- GitHub auth cannot dispatch the workflow;
- AWS access cannot read the bootstrap outputs;
- repo/ref differs from `amitkarpe/aws-secops` + `main`;
- a proposed fix would widen IAM/OIDC/tool authority.

Do not deploy the Harness directly with an administrator AWS session as a substitute for the GitHub OIDC workflow.

## Acceptance

1. All four variable names are configured.
2. `AWS operator Harness deploy` is dispatched from `main`.
3. Workflow reaches success and the exact Harness stack reaches a successful terminal state.
4. No Demo v1 mutation occurs.
5. X posts `HANDOFF: CHATGPT` with the public-safe evidence and requests independent AWS Core verification.
