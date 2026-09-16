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
- PR #61 merged the Issue #60 contextual-investigation / Decision Timeline implementation, but live activation is gated by Issue #62 correctness hardening.

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

Implementation package: **PR #61** (merged).

Correctness gate: **Issue #62 / PR #63**.

## Issue #62 correction

Post-merge review found that PR #61 sampled one batch item's `before` value as provider state. The correction must be merged before live activation:

1. aggregate the whole durable S3 batch;
2. treat `before` only as pending preview/precondition evidence;
3. treat terminal `COMPLETED` / `SKIPPED` `after` values as provider remediation truth;
4. return mixed/partial/unknown instead of a fleet-wide conclusion when evidence is incomplete;
5. hard-allowlist the two-account AWS read helper to STS identity + Config compliance summary only;
6. keep IAM least-privilege as a separate runtime verification claim.

## Current next action

Complete PR #63 with credential-free regression CI. Do **not** activate the new investigation/timeline tools or claim the two-account milestone live until #62 is merged and later runtime acceptance under #60 explicitly passes.

No AWS deployment, IAM/OIDC/Gateway/Policy change, or cross-account mutation is part of #62.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
