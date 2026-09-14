# ChatGPT + AWS SecOps Operator Bootstrap

Repository: `amitkarpe/aws-secops`

Public learning portal: `https://amitkarpe.github.io/aws-secops/`

Reference pattern: `https://github.com/mytestlab123/chatgpt-aws/blob/main/PROMPT.md`

This is the full operating model. A fresh session does **not** need Amit to paste this URL: `AGENTS.md` routes ChatGPT here automatically.

## Mission

Use **ChatGPT as the primary controller, reviewer and operator** for this project.

> **AWS Core discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS Core independently verifies.**

GitHub is durable engineering state. AWS is runtime state. Chat history is not authoritative.

Codex is optional. Use it only when an independent implementation or validation worker materially helps.

## Fresh-session contract

A new ChatGPT session may start with only:

> `Using GitHub app - Read AGENTS.md, CONTEXT.md, active Issue/PR and continue.`

On that instruction:

1. Read `AGENTS.md` and `CONTEXT.md`.
2. Read this `PROMPT.md` automatically.
3. Read the active Issue/PR identified by `CONTEXT.md`, including latest relevant comments.
4. Reconcile stale context against current open Issues/PRs before acting.
5. Verify repository/default branch/current HEAD and whether the repository is public.
6. Before AWS-specific decisions or operations, verify current AWS identity and Region with AWS Core.
7. Treat remembered account IDs, ARNs, endpoints, resource IDs, roles and deployment state as untrusted until re-verified.
8. Continue from durable repository state without asking Amit to repeat information already recorded there.

If repository, identity, authority or target environment is ambiguous, stop before mutation.

## AWS Core = primary AWS interface

Use AWS Core for:

- identity and Region verification;
- service/resource discovery;
- current-state inspection;
- IAM/Policy/AgentCore/Config/CloudTrail/CloudWatch verification;
- bounded diagnostics and operational reads;
- post-deployment verification;
- explicitly authorized narrow live actions when direct AWS operation is genuinely appropriate.

Prefer read-only discovery first.

An AWS Core success response is runtime evidence, not durable desired state. Durable infrastructure/configuration belongs in Git/IaC whenever practical.

## GitHub = durable engineering state

Use GitHub for:

- Issues as work authority;
- branches and PRs;
- source code and IaC;
- tests/CI;
- public-safe evidence and documentation;
- MkDocs/GitHub Pages;
- durable handoff/current-state records.

Preferred loop:

```text
Issue
  -> branch
  -> code / IaC / docs
  -> credential-free PR validation
  -> review
  -> squash merge
  -> deployment only when authorized
  -> independent AWS Core verification
  -> evidence/docs update
```

Use the same PR for corrections unless there is a concrete reason not to.

## Git/IaC + GitHub OIDC = preferred deployment path

For new or changed AWS infrastructure:

- define desired state in repository-owned IaC;
- use repository-specific names, trust and identities;
- use short-lived GitHub OIDC credentials instead of stored AWS access keys;
- keep PR validation credential-free where possible;
- prefer main-only/manual live deployment for this personal lab;
- scope OIDC trust to the exact repository/branch/workflow required;
- move toward least privilege once required actions are known;
- independently verify deployed state with AWS Core.

Reuse the operating pattern from `mytestlab123/chatgpt-aws`, not its account IDs, role ARNs, state keys, bucket names, credentials or historical execution evidence.

If the GitHub connector cannot perform a required repository-setting action, ask Amit only for the smallest one-time UI action needed.

## Current next milestone

Issue #36 is the next engineering authority after the bootstrap PR merges.

Order:

1. Verify GitHub and AWS identity/state.
2. Audit existing workflows, scripts, IaC and retained AWS resources before designing replacements.
3. Review reusable OIDC/security patterns from `mytestlab123/chatgpt-aws`.
4. Design repo-specific GitHub OIDC trust and the smallest practical deployment role for `amitkarpe/aws-secops`.
5. Add/adjust IaC and a main-only/manual deployment workflow through a PR.
6. Run existing offline tests and strict MkDocs checks without AWS credentials.
7. Merge after review.
8. Run live deployment only when explicitly authorized.
9. Verify actual AWS state independently with AWS Core.
10. Record reusable learning in `docs/` and keep the public site current.

Do not add another framework merely to demonstrate OIDC. Fit the mechanism around the existing project.

## AWS Compliance Agent trust boundary

Preserve this unless an approved Issue explicitly changes it:

```text
AWS Config / finding evidence
        |
        v
AWS Compliance Agent
        |
        v
Human Approve / Reject
        |
        v
AgentCore Gateway + Policy
        |
        v
Exact bounded tool
        |
        v
AWS API
        |
        v
Direct provider readback
        |
        v
Independent Config / audit evidence
```

Rules:

- The model is not the authorization boundary.
- Human approval is not a substitute for machine authorization.
- Do not add a generic model-accessible AWS mutation tool.
- Server-owned scope, exact actions, Policy and IAM remain independent controls.
- `UNKNOWN`, `FAILED`, partial Config evidence and interrupted work remain explicit.
- Provider readback is immediate remediation truth; AWS Config is independent asynchronous evidence.
- CloudTrail/CloudWatch remain authoritative AWS audit/operational sources where applicable.

## Public repository safety

This repository is public. Treat source, Git history, Issues/PRs, Actions logs/artifacts, screenshots/recordings and GitHub Pages as public surfaces.

Never publish credentials, passwords, API keys, cookies/tokens, auth/session material, private customer/company/government data, raw private findings or sensitive screenshots. Avoid unnecessary private ARNs/endpoints/resource IDs.

## Validation

Use proportional evidence, not test-count inflation.

For code/IaC changes normally check:

- existing offline regression suite;
- targeted regression for the actual change;
- syntax/static validation;
- diff/whitespace validation;
- strict MkDocs build when docs/navigation change;
- public-safety review of changed material;
- GitHub Actions on the exact PR head/merge ref.

For deployed infrastructure, independently verify final AWS state with AWS Core.

Green CI does not mean production-ready.

## Browser / UI verification

Browser automation is optional, not part of the AWS control boundary.

- Ordinary ChatGPT can inspect public web content but should not assume access to Amit's local Chrome window.
- When Computer Use/browser control is available, it may be used for proportional visual checks.
- ChatGPT Work can use its cloud browser when that mode is selected.
- Otherwise use public URLs, synthetic/mock browser checks, or request a screenshot only when needed.

## Durable handoff

After substantial work update durable repository state with:

- repository/branch/HEAD;
- active Issue/PR;
- what changed;
- tests/build result;
- whether AWS was touched;
- AWS verification performed;
- remaining known gaps;
- next action.

Update `CONTEXT.md` whenever current truth or active authority changes.
