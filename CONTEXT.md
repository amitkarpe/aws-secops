# Agent Context

This file is compact **current-only** state for ChatGPT/coding-agent continuity.

Repository: `amitkarpe/aws-secops`

## Current product truth

- Demo v1 live acceptance remains recorded for the personal Singapore lab.
- Supported remediation families remain S3 Block Public Access and restricted SSH on retained owned demo resources.
- Approved execution remains human approval -> Gateway/Policy -> exact family tool -> provider readback.
- The model has no generic AWS mutation tool.
- The `aws_secops_operator` Harness is deployed and independently verified as the read-only operator reasoning/read layer for the two existing AWS Config controls.
- Explicit `fix/apply/execute` requests do not mutate through the Harness; they route to the existing governed human-approval path.
- Issue #58 / PR #59 operator-summary polish is complete.

## Current operating model

> **AWS Core discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS Core independently verifies.**

ChatGPT Web is the default controller. GitHub is durable engineering state. AWS MCP/Core is the live AWS discovery and verification path. Codex is used only when deeper implementation or independent runtime validation materially helps.

## Verified baseline

- one `aws_secops_operator` Harness in `ap-southeast-1`;
- Nova 2 Lite;
- exact two read-only AWS Config tools through AgentCore Gateway;
- Gateway Policy mode `ENFORCE`;
- read Lambda has no S3/EC2/SSM mutation authority;
- live Config summary + focused findings reads passed for both supported controls;
- negative `fix/apply/execute` boundary passed;
- Demo v1 mutation path remains separate and governed.

## Current authority

**Issue #60 — next agentic SecOps phase**

https://github.com/amitkarpe/aws-secops/issues/60

Implementation PR:

**PR #61 — Issue #60: plan next agentic SecOps phase**

https://github.com/amitkarpe/aws-secops/pull/61

## Current implementation

PR #61 now implements the bounded next-phase slice rather than remaining planning-only:

1. Contextual S3 investigation from existing Config/retained-scope/provider evidence.
2. Factual Agent Decision Timeline with no hidden chain-of-thought.
3. Exactly-two-account read-only Config summary code with raw account IDs hidden by default; live second-account proof is still pending explicit configuration.
4. A 2–3 minute agentic SecOps demo script.
5. Regression tests preserving the existing human approval -> Gateway/Policy -> exact tool -> provider readback mutation boundary.

## Current next action

Run/inspect credential-free PR validation for PR #61, fix any regression in the same PR, and review the final diff. Do not deploy AWS resources or widen IAM/OIDC/Gateway/Policy while validating this PR.

After merge, any live activation or two-account runtime proof is a separate authorized step and must be independently verified with AWS Core.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
