# GitHub OIDC bootstrap — Issue #36

## Goal

Establish a repository-specific GitHub OIDC identity for `amitkarpe/aws-secops` without changing the existing Demo v1 runtime.

## Trust boundary

The bootstrap role trusts only the exact GitHub Actions subject observed for this repository's `main` branch:

`repo:amitkarpe@1894622/aws-secops@1362357126:ref:refs/heads/main`

The expected audience is `sts.amazonaws.com`.

The immutable GitHub owner/repository IDs in the subject were confirmed from GitHub metadata and the failed STS web-identity event. Do not broaden this to an organization or repository wildcard merely to make OIDC succeed.

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

## OIDC troubleshooting rule

Follow the repository reference model in `mytestlab123/chatgpt-aws/PROMPT.md` and `docs/learning/github-oidc.md`:

1. confirm the workflow has job-scoped `id-token: write`;
2. verify the AWS OIDC provider and `sts.amazonaws.com` audience;
3. inspect the actual web-identity subject in CloudTrail when `AssumeRoleWithWebIdentity` fails;
4. compare it with the role trust policy;
5. update trust only to the exact legitimate subject observed;
6. never replace precise trust with a broad organization wildcard as a troubleshooting shortcut.

The first live preflight failure for this repository was caused by using the older name-only subject form in IAM trust while GitHub issued the ID-qualified subject above.

## Codex / local operator path

When ChatGPT's GitHub connector cannot write repository variables or dispatch a workflow, Codex or another trusted local operator may use `scripts/run-oidc-preflight.sh`.

The helper:

1. derives the current AWS account ID and the preflight role ARN locally;
2. writes them to GitHub repository variables without printing their values;
3. verifies the two variable names only;
4. dispatches `aws-oidc-preflight.yml` from `main`;
5. waits for completion and prints only the workflow result metadata.

It requires authenticated `aws` and `gh` CLIs and must be run only for the repository/role already authorized by Issue #36. It does not deploy or remediate Demo v1 resources.

If the helper fails, inspect the failed workflow step only as needed. Do not paste account IDs, role ARNs, credentials, or other private identifiers into public Issues, PRs, comments, committed files, or logs.

Any later expansion from read-only preflight to deployment permissions requires explicit review under Issue #36 and must preserve the existing human approval -> AgentCore Gateway/Policy -> exact remediation tool boundary.
