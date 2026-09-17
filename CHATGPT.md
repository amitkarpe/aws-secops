# ChatGPT-Codex Collaboration

Purpose: keep Amit, ChatGPT, Codex, GitHub, and AWS work coordinated with minimal handoff overhead.

Canonical collaboration protocol:
https://github.com/amitkarpe/work/blob/main/docs/chatgpt/CHATGPT_COLLABORATION_PROTOCOL.md

Reusable starter guidance:
https://github.com/amitkarpe/repo-starter/blob/main/CHATGPT.md

## Default behavior

When the current objective is known, `go`, `g`, `.`, `Y`, `yes`, or equivalent affirmative continuation means: fetch current durable GitHub state and execute the approved objective within existing authority and constraints.

Do not restart planning unless Amit explicitly asks for `plan`, `review`, `discuss`, or a decision. Stop only for a real safety, scope, authorization, repository-identity, access, or validation blocker.

`G` = ChatGPT. `X` = Codex. `M` = AWS MCP. `O` = GitHub OIDC.

Amit is the decision-maker, not the copy/paste transport layer. G and X should fetch the owning Issue, PR, comments, current HEAD, validation state, and relevant runtime evidence themselves when accessible.

## Repository binding

Primary repository: `amitkarpe/aws-secops`.

Before writes or implementation, resolve the repository that owns the current objective and confirm that the active Issue/PR belongs to that repository. Reading related repositories is allowed. Cross-repository writes require Amit's explicit instruction or an active Issue/SPEC that clearly authorizes them.

Never mutate another repository merely because it is related or recently active.

## Issue + PR ownership rule

For implementation-ready work where repository changes are expected:

1. G creates the owning Issue.
2. G creates the implementation branch and starter PR immediately.
3. The starter PR may be Draft when implementation is incomplete.
4. X continues in that existing PR; X must not create a replacement PR for the same milestone unless scope materially changes.
5. X implements, validates, and leaves one compact `HANDOFF: CHATGPT` on the PR.
6. G reviews the complete PR, handles corrections in the same PR where practical, and merges when eligible and authorized.

Use Issue-only handoff only for research/planning/decision-only work or when no repository change is expected.

Goal: Amit should not be the transport layer between G and X.

## Handoff format

Use the active PR as the normal durable handoff; use the owning Issue only when no PR should exist yet.

Before acting, fetch current PR HEAD and latest relevant handoff/comment. Reconcile stale state before implementation.

Return handoffs should stay compact:

- `HANDOFF: CODEX` or `HANDOFF: CHATGPT`
- `Head: <sha>` when relevant
- `Result: PASS | PARTIAL | BLOCKED | FAIL | N/A`
- `Next: <one action>`
- `Accept: <one condition>` when useful

When a handoff is presented to Amit for copy/paste into X/another session, put the complete handoff in one fenced Markdown block.

## Milestone economy

Follow KISS: optimize for one useful outcome, not the smallest possible PR.

Prefer one cohesive milestone containing roughly 2-3 related phases/tasks when they share one outcome and acceptance path. Do not split implementation, tests, docs, configuration, and directly related corrections into micro-PRs merely because individual edits are small.

Use proportional validation. Reuse existing tests, scripts, docs, and proof paths before adding new machinery.

## aws-secops operating model

ChatGPT is the default controller/reviewer/operator.

> AWS MCP discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS MCP independently verifies where the runtime supports it.

For personal LAB/DEV multi-account discovery, broad read/audit access is acceptable when it improves demo velocity. Broad mutation is not implied by broad read access.

Current cross-account read design uses a fixed M-visible hub principal plus `sts:AssumeRole` to same-name `ChatGPTCrossAccountReadRole` targets. The IAM path is proven; current M runtime does not yet support carrying assumed-role credentials into later MCP calls. Do not claim dynamic MCP account switching until that runtime capability exists.

Cross-account remediation remains separate authority and must not be inferred from read access.

## Safety

- Never commit credentials, tokens, private keys, session state, customer data, or raw secrets.
- Treat this repository, Git history, Issues/PRs, Actions output, and Pages as public.
- Preserve the governed remediation boundary defined in `SPEC.md`.
- Repository write access does not imply AWS mutation authority.
- Explicit no-merge, destructive, production, credential, publication, and security gates remain binding.

## Connector safety gate

For an already-authorized bounded connector action:

1. re-read the exact repository/branch/PR/target and current state;
2. retry the identical bounded action at most once with scope unchanged;
3. if blocked again, stop connector retries and report `BLOCKED_CONNECTOR_SAFETY`;
4. continue through the existing Issue/PR handoff to X/local tooling only when that path is already authorized.

Never widen permissions, weaken safeguards, change repository/branch, create a replacement handoff, or switch reasoning mode merely to bypass a connector safety block.
