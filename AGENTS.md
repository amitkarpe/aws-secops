# AGENTS.md

Repository: `amitkarpe/aws-secops`

## Read order

1. `AGENTS.md`
2. `CONTEXT.md`
3. `INIT.md` only when repository initialization is incomplete or Amit explicitly asks to reinitialize
4. `CHATGPT.md` for ChatGPT/Codex/GitHub collaboration
5. `ENV.md` when runtime, cloud, host, profile, or tool facts matter
6. `PROMPT.md` for the aws-secops ChatGPT + GitHub + AWS MCP operating model
7. `SPEC.md` before implementation, mutation, deployment, cleanup, or trusted-contract changes
8. `ROADMAP.md` when selecting future scope

## Fresh ChatGPT session

A new ChatGPT session may begin with only:

> `Using GitHub app - Read AGENTS.md, CONTEXT.md, active Issue/PR and continue.`

Treat that as a complete bootstrap instruction.

The session must:

1. Read `AGENTS.md` and `CONTEXT.md` first.
2. Follow the read order above only as needed for the current objective; do not reload everything on every handoff.
3. Use `CONTEXT.md` to identify the current authority. Read the referenced active Issue/PR and their latest relevant comments. If repository state has moved, reconcile current GitHub truth before acting.
4. Verify GitHub repository/default branch/current HEAD before changes. Before AWS-specific decisions or operations, verify the current AWS identity and Region with AWS MCP where supported.
5. Continue from durable state without asking Amit to repeat context already available in the repository or owning Issue/PR.

If multiple open work items exist, do **not** guess. `CONTEXT.md` names the current authority; otherwise report the ambiguity before mutation.

## Operating model

ChatGPT is the primary controller, reviewer, and operator.

> **AWS MCP discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS MCP independently verifies where the runtime supports it.**

GitHub is durable engineering state. AWS is runtime state. Chat history is not authoritative.

Codex is optional. Use X for cohesive implementation/runtime packages that materially benefit from local/profile/runtime access or deeper engineering; do not hand X isolated one-command checks that G can perform directly.

For implementation-ready work where repository changes are expected, follow `CHATGPT.md`: G creates the owning Issue, branch, and starter PR; X continues that PR; G reviews and merges.

## Rules

- Follow KISS: one useful milestone, one happy path, proportional proof, one usable result.
- Preserve existing work. Do not revert unrelated changes or use destructive Git commands without explicit approval.
- Keep durable code, decisions, and evidence in Git. Never commit secrets, credentials, auth/session material, private findings, or unnecessary private infrastructure identifiers.
- Treat this repository, Git history, Issues/PRs, Actions logs/artifacts, and GitHub Pages as public.
- Keep `CONTEXT.md` current-only. It is the restart index, not project history.
- Update `CONTEXT.md` when repository identity, current truth, active Issue/PR, blocker, or next action materially changes.
- `SPEC.md` is the repository execution/security contract. Proceed inside ACTIVE approved scope and stop on a genuine safety, scope, authorization, repository-identity, access, or validation failure.
- Prefer read-only discovery before mutation.
- Use repository-owned IaC for durable AWS desired state whenever practical.
- Prefer short-lived, repo-specific GitHub OIDC credentials over stored AWS access keys.
- Keep PR validation credential-free where possible. Live deployment should be main-only/manual for this lab unless an approved Issue changes that contract.
- Preserve the AWS Compliance Agent security boundary: human approval, AgentCore Gateway/Policy, exact bounded tools, provider readback; no generic model-accessible AWS mutation tool.
- For personal LAB/DEV multi-account discovery, broad read/audit access is acceptable for demo velocity; broad mutation is not implied.
- Explain the intended AWS change before live mutation. Get explicit confirmation for destructive or irreversible actions.
- Use proportional validation that matches changed behavior and risk; avoid duplicate validators that add little confidence.
- The Connector Safety Gate in `CHATGPT.md` is mandatory for connector/platform actions.
- When the current objective is known, `go`, `g`, `.`, `Y`, or `yes` means execute/continue it within existing authority unless Amit explicitly selected plan/review/discussion mode.
- Before cross-repo mutation, apply the repository-binding guard in `CHATGPT.md`.

## Sensitive GitHub / AWS writes

For IAM, OIDC, GitHub Actions credentials, deployment roles, or other security-sensitive changes:

1. Re-read the exact target file, branch, and PR immediately before writing.
2. Change one security boundary at a time.
3. Prefer one atomic file write, then re-fetch and verify it.
4. Do not bundle unrelated IAM + workflow + deployment mutation into one step.
5. If a write is safety-blocked:
   - do not broaden permissions or weaken safeguards;
   - re-read the unchanged target;
   - retry the identical bounded write once;
   - if still blocked, stop and report `BLOCKED_CONNECTOR_SAFETY`.
6. Distinguish safety blocks from approval prompts, stale SHA/409 errors, GitHub permission failures, and validation failures.
7. A repository write does not authorize AWS mutation.

Detailed observations and the experiment log live in `docs/research/CHATGPT_CONNECTOR_SAFETY_FRAMING.md`.

## Git workflow

For non-trivial implementation work prefer:

```text
Issue created by G
  -> implementation branch created by G
  -> starter PR created by G
  -> X/G implementation + validation in same PR
  -> HANDOFF: CHATGPT
  -> G review
  -> squash merge when eligible
  -> deployment only when authorized
  -> independent AWS MCP verification where supported
  -> evidence/docs update
```

Use the existing PR for corrections. Do not create parallel replacement PRs for the same milestone unless scope or trust boundary materially changes.

Batch local workspace cleanup after roughly 5-10 merged PRs or a major milestone; do not clean after every PR. Preserve active work and referenced evidence. Remote branch or cloud-resource cleanup is separate authority.
