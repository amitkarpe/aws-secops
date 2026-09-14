# ChatGPT GitHub connector safety-framing experiment

Updated: 2026-09-14

## Purpose

Record what we observed while adding GitHub OIDC + AWS IAM changes for Issue #36, without treating a small number of attempts as proof of how the platform safety system works.

This document is an **experiment log and working hypothesis**, not a description of OpenAI's internal safety implementation.

## Observed behaviour

During the same Issue #36 task we saw several different outcomes from closely related GitHub writes:

1. A branch creation succeeded.
2. Initial attempts to commit AWS IAM/OIDC infrastructure were blocked with:

   `This tool call was blocked by OpenAI's safety checks. Please double check what you are sending.`

3. A later atomic write of the repository-specific OIDC/IAM bootstrap succeeded.
4. Initial attempts to add a workflow containing job-scoped `id-token: write` were blocked.
5. A later atomic retry of the same bounded, read-only OIDC preflight workflow succeeded.
6. A later update attempt returned HTTP 409 because the file SHA was stale. Re-reading the branch showed another successful write had already moved the file. This was a normal GitHub concurrency/version error, **not** a safety block.
7. With user-selected Extra High thinking effort, a new atomic static-safety test file was committed successfully and then re-fetched successfully. The test file makes no AWS calls and grants no permissions.

No AWS mutation was performed during these observations.

## What we can conclude

We can conclude only the following from the observed evidence:

- the IAM/OIDC repository writes were **not categorically impossible** through the GitHub connector;
- some attempts were blocked by a connector/platform safety check;
- later, more narrowly scoped attempts succeeded;
- ordinary GitHub errors such as a stale file SHA can look like another failure but have a different cause;
- a successful later attempt does **not** prove that thinking effort alone caused the change in result.

## Working hypothesis

The most useful hypothesis to test is that sensitive infrastructure changes are more reliable when the task is framed and executed as small, independently reviewable operations.

Possible contributing variables include:

1. how many security-sensitive operations are bundled into one request;
2. how clearly the intended permission boundary is stated;
3. whether the change is read-only, mutating, or mixes both;
4. whether repository/account/branch authority was verified first;
5. whether the exact current file state was re-read immediately before a write;
6. reasoning/thinking effort;
7. normal variability in a borderline safety classification.

We do **not** currently have enough controlled trials to rank these variables confidently.

## Recommended operating protocol

For GitHub + AWS + IAM/OIDC work, use this sequence:

```text
1. VERIFY
   - exact repository
   - current branch / PR
   - current file SHA/state
   - AWS identity and Region when relevant

2. DEFINE ONE BOUNDARY
   - one role or one workflow or one policy change
   - explicitly state what it cannot do

3. WRITE ONE ATOMIC CHANGE
   - one file where practical
   - no unrelated refactor

4. VERIFY THE WRITE
   - re-fetch the file / PR
   - distinguish safety block vs GitHub/API error

5. CONTINUE TO THE NEXT CHANGE
   - only after the previous boundary is verified

6. AWS APPLY IS SEPARATE
   - repository write != AWS deployment
   - require the repository's normal approval/merge/bootstrap process
```

## Safety-framing prompt

Use this when a GitHub/AWS change is sensitive:

```markdown
Use the existing repository authority and make only the smallest bounded change for this step.

Before writing:
1. Re-read the exact target file/branch/PR state.
2. State the single security boundary being changed.
3. Confirm what this step explicitly does NOT authorize or execute.

Then:
4. Perform one atomic repository write.
5. Re-fetch and verify it.
6. Stop before the next security boundary unless the previous step succeeded.

If a tool call fails, classify the failure first:
- user approval required,
- connector/platform safety block,
- GitHub permission failure,
- stale SHA/concurrency error,
- validation/syntax error,
- other.

Do not broaden permissions merely to make the operation pass.
Do not treat a repository write as approval to mutate AWS.
```

## Thinking-effort experiment

Amit observed that the workflow became more reliable after increasing thinking effort. This is worth testing, but the experiment must avoid confusing correlation with causation.

For future comparable tasks, record:

| Trial | Thinking effort | Change size | Sensitive boundary | Result | Failure class |
| --- | --- | --- | --- | --- | --- |
| A | lower/default | bundled or initial | IAM/OIDC | observed block | safety check |
| B | Medium | atomic IAM file | IAM/OIDC trust + read-only role | success | none |
| C | Medium | atomic workflow | `id-token: write` + read-only OIDC | initial block, later success | safety check / none |
| D | Extra High (user-selected) | atomic validation change | static safety tests only | success + readback verified | none |

Trial D supports the atomic-execution hypothesis, but it is **not a controlled proof** that Extra High thinking caused the success because the requested change was safer than the IAM/OIDC writes in Trials B/C.

To learn anything useful, keep the requested change as similar as possible between future trials and record the exact failure category.

## KISS rule for this repository

For security-sensitive ChatGPT -> GitHub work:

> **One verified boundary, one atomic write, one readback. Then continue.**

For durable AWS delivery, the repository's existing rule still applies:

> **MCP discovers and verifies; Git/IaC declares; OIDC CI/CD applies.**
