# AGENTS.md

Repository: `amitkarpe/aws-secops`

## Bootstrap / Recovery

A new ChatGPT session may begin with only:

> `Using GitHub app - Read AGENTS.md, CONTEXT.md, active Issue/PR and continue.`

Treat that as a complete bootstrap instruction when the session lacks usable repository context, governing files materially changed, or state is stale/incomplete/contradictory.

For normal continuation, use the named Issue/PR as the execution packet, its latest relevant authorized comment/handoff as the delta, and fetch current HEAD before acting. Do not force a full `AGENTS.md` / `CONTEXT.md` / `PROMPT.md` reload on every handoff.

For bootstrap/recovery the session must:

1. Read `AGENTS.md` and `CONTEXT.md` first.
2. Read `PROMPT.md` automatically for the full ChatGPT + GitHub + AWS Core operating model; the user does not need to mention it separately.
3. Use `CONTEXT.md` to identify the current authority. Read the referenced active Issue/PR and their latest relevant comments. If repository state has moved, re-discover open Issues/PRs and reconcile `CONTEXT.md` before acting.
4. Read `SPEC.md` when work changes a trusted contract, release, environment, AWS state, or external system. Read `ROADMAP.md` when selecting future scope.
5. Verify GitHub repository/default branch/current HEAD before changes. Before AWS-specific decisions or operations, verify the current AWS identity and Region with AWS Core.
6. Continue from the current durable state without asking Amit to repeat context that is already in the repository.

If multiple open work items exist, do **not** guess. `CONTEXT.md` names the current authority; otherwise report the ambiguity before mutation.

## Operating model

ChatGPT is the primary controller, reviewer and operator.

> **AWS Core discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS Core independently verifies.**

GitHub is durable engineering state. AWS is runtime state. Chat history is not authoritative.

Codex is optional. Use it only when an independent implementation or validation worker materially helps; it is not required for normal operation.

## Rules

- Follow KISS: one useful milestone, one happy path, proportional proof, one usable result.
- Prefer read-only discovery before mutation.
- Preserve existing work. Do not revert unrelated changes or use destructive Git commands without explicit approval.
- Keep durable code, decisions and evidence in Git. Never commit secrets, credentials, auth/session material, private findings or unnecessary private infrastructure identifiers.
- Treat this repository, Git history, Issues/PRs, Actions logs/artifacts and GitHub Pages as public.
- Use repository-owned IaC for durable AWS desired state whenever practical.
- Prefer short-lived, repo-specific GitHub OIDC credentials over stored AWS access keys.
- Keep PR validation credential-free where possible. Live deployment should be main-only/manual for this lab unless an approved Issue changes that contract.
- Preserve the AWS Compliance Agent security boundary: human approval, AgentCore Gateway/Policy, exact bounded tools, provider readback; no generic model-accessible AWS mutation tool.
- Explain the intended AWS change before live mutation. Get explicit confirmation for destructive or irreversible actions.
- Update `CONTEXT.md` whenever current truth, active authority or next action changes.
- Keep `SPEC.md` as the current trusted contract; historical proofs belong under `docs/`.

## Sensitive GitHub / AWS writes

For IAM, OIDC, GitHub Actions credentials, deployment roles, or other security-sensitive changes:

1. Re-read the exact target file, branch, and PR immediately before writing.
2. Change one security boundary at a time.
3. Prefer one atomic file write, then re-fetch and verify it.
4. Do not bundle IAM + workflow + deployment mutation into one step.
5. If a write is safety-blocked:
   - do not broaden permissions or weaken safeguards;
   - re-read the unchanged target;
   - retry the identical bounded write once;
   - if still blocked, stop and report it.
6. Distinguish safety blocks from approval prompts, stale SHA/409 errors, GitHub permission failures, and validation failures.
7. A repository write does not authorize AWS mutation.

Detailed observations and the experiment log live in `docs/research/CHATGPT_CONNECTOR_SAFETY_FRAMING.md`.

## Git workflow

For non-trivial work prefer:

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

Use the existing PR for corrections. Do not create parallel replacement PRs for the same milestone unless necessary.
