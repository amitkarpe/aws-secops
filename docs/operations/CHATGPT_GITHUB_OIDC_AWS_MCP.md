# ChatGPT + GitHub App + GitHub OIDC + AWS MCP

This guide explains how this repository separates **repository access**, **AWS deployment credentials**, and **live AWS verification**.

> **Core model:** AWS MCP discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS MCP independently verifies.

## Architecture

```text
                    ChatGPT
                      |
                      | GitHub App / connector
                      v
                 GitHub repository
           Issues / PRs / code / IaC
                      |
                      | GitHub Actions
                      | OIDC short-lived token
                      v
                 AWS IAM role
                      |
                      v
                AWS deployment
                      |
                      | independent readback
                      v
                   AWS MCP
                      ^
                      |
                ChatGPT runtime
```

There are three separate trust paths.

## 1. ChatGPT -> GitHub: GitHub App

ChatGPT uses the connected GitHub App/connector to work with repository state.

Typical operations:

- read files and PRs;
- create Issues and branches;
- edit repository files;
- open/review/merge PRs where connector permissions allow;
- inspect workflow runs and logs.

This path does **not** use AWS OIDC and does not require AWS credentials.

Repository access does not authorize AWS mutation.

## 2. GitHub Actions -> AWS: GitHub OIDC

GitHub OIDC is used by GitHub Actions jobs that need AWS access.

The workflow requests a short-lived OIDC identity token and exchanges it for temporary AWS role credentials through AWS STS.

This avoids storing long-lived AWS access keys in GitHub.

Required workflow permission:

```yaml
permissions:
  contents: read
  id-token: write
```

Current examples:

- `.github/workflows/aws-oidc-preflight.yml`
- `.github/workflows/aws-deploy-canary.yml`
- `.github/workflows/aws-deploy-operator-harness.yml`

The expected flow is:

```text
main/manual workflow
    ->
GitHub OIDC token
    ->
repo-scoped AWS IAM trust
    ->
temporary AWS role credentials
    ->
bounded deployment
```

The AWS role and IAM trust policy remain the AWS authorization boundary.

## 3. ChatGPT -> AWS: AWS MCP

AWS MCP/Core is a separate live control-plane connection used for:

- STS identity verification;
- service/resource discovery;
- Config, IAM, CloudTrail, CloudWatch and AgentCore inspection;
- bounded diagnostics;
- independent post-deployment verification;
- explicitly authorized narrow operations where supported.

Before AWS work:

1. select the intended AWS MCP connection;
2. run STS `GetCallerIdentity`;
3. verify Region;
4. keep the operation bound to that connection.

A successful AWS MCP read proves connectivity only. It does not grant mutation authority.

## Normal engineering flow

```text
Issue
  -> branch
  -> code / IaC
  -> PR validation
  -> review
  -> squash merge
  -> manual/main GitHub Actions deployment
  -> GitHub OIDC assumes bounded AWS role
  -> AWS change
  -> AWS MCP independent verification
  -> evidence/docs update
```

Use repository-owned IaC for durable desired state whenever practical.

## Why no long-lived AWS keys are needed

The preferred model uses two short-lived/session-based mechanisms:

- GitHub Actions obtains temporary AWS credentials through OIDC.
- ChatGPT uses the separately connected AWS MCP runtime.

Do not commit:

- AWS access keys;
- session tokens;
- GitHub tokens;
- browser cookies;
- connector credentials;
- private keys.

## Billing and usage limits

GitHub Actions billing is separate from GitHub App repository operations.

| Operation | Needs GitHub Actions runner time? |
|---|---:|
| ChatGPT reads GitHub files | No |
| Create/update Issue or PR | No |
| Edit repository files through GitHub App | No |
| Review/merge a PR | No |
| AWS MCP discovery/verification | No |
| Run an OIDC preflight workflow | Yes |
| Deploy AWS through a GitHub Actions OIDC workflow | Yes |
| Run CI/test workflows | Yes |

A GitHub Actions billing/usage restriction therefore does **not** stop ChatGPT from continuing repository work through the GitHub App.

It can block or delay steps that require an Actions runner, such as:

- OIDC-based deployment;
- hosted CI;
- workflow-only validation.

Billing behavior depends on repository visibility, runner type and the GitHub plan. Check current GitHub billing documentation before treating any allowance as permanent product behavior.

## If GitHub Actions cannot run

Fail closed for deployment.

Do **not** replace GitHub OIDC by committing long-lived AWS credentials.

Use this order:

1. continue repository work through the GitHub App;
2. run credential-free/static validation where available;
3. use AWS MCP for read-only discovery and verification;
4. leave the PR unmerged or deployment pending when an OIDC deployment proof is required;
5. use a separately approved local/manual deployment path only if the owning Issue/SPEC explicitly permits it.

Never weaken IAM/OIDC trust just to bypass an Actions/billing limitation.

## Onboarding another engineer or ChatGPT session

Start with:

```text
Using GitHub app - Read AGENTS.md, CONTEXT.md, active Issue/PR and continue.
```

Then verify:

1. correct repository: `amitkarpe/aws-secops`;
2. current `main` and active Issue/PR;
3. GitHub App repository access;
4. intended AWS MCP connection and STS identity;
5. OIDC workflow role/variables before any GitHub Actions deployment.

Read these files when needed:

- `AGENTS.md`
- `CONTEXT.md`
- `CHATGPT.md`
- `PROMPT.md`
- `SPEC.md`
- this guide

## Troubleshooting

### ChatGPT can edit GitHub but AWS deployment fails

Likely GitHub App access is fine and the problem is in the Actions/OIDC/AWS role path.

Check:

1. workflow is running from the expected repository/branch;
2. `id-token: write` is present;
3. expected AWS role variable is configured;
4. OIDC trust matches repository/branch/environment conditions;
5. STS caller account matches the allowed account;
6. runner billing/usage has not blocked the workflow.

### GitHub Actions works but ChatGPT cannot edit files

That is a GitHub App/connector permission problem, not an OIDC problem.

Check the repository installation and connector permissions.

### AWS MCP works but GitHub OIDC fails

AWS MCP and GitHub OIDC are independent identities.

A successful MCP STS call does not prove the GitHub Actions role trust is correct.

Use `aws-oidc-preflight.yml` to test the OIDC path.

### OIDC works but AWS MCP verification fails

Treat deployment and verification as separate control planes.

Verify the AWS MCP connection, selected account and Region independently.

### Actions billing is exhausted or restricted

Repository work can continue through GitHub App.

Do not claim deployment success until the required Actions/OIDC path or another explicitly authorized deployment path runs successfully.

## Security boundaries

Keep these independent:

```text
GitHub App permission
    !=
GitHub OIDC AWS role permission
    !=
AWS MCP permission
    !=
Compliance Agent native human approval
```

One working path does not imply authority on another.

For the Compliance Agent specifically, preserve:

```text
finding evidence
  -> exact frozen scope
  -> native human Approve/Reject
  -> bounded executor
  -> AWS service readback
  -> independent Config convergence
```

## Quick reference

| Component | Purpose | Credential model |
|---|---|---|
| GitHub App | ChatGPT repository access | managed connector/app session |
| GitHub Actions | CI/deployment runtime | runner |
| GitHub OIDC | GitHub Actions -> AWS identity | short-lived OIDC/STS credentials |
| AWS MCP | ChatGPT live AWS access | connected AWS control-plane session |
| Git/IaC | durable desired state | repository content |
| AWS IAM | AWS authorization boundary | roles/policies/trust |

## Related files

- `AGENTS.md`
- `CHATGPT.md`
- `PROMPT.md`
- `.github/workflows/aws-oidc-preflight.yml`
- `.github/workflows/aws-deploy-canary.yml`
- `.github/workflows/aws-deploy-operator-harness.yml`
