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

Implementation package: **PR #61**.

## Issue #60 implementation state

The bounded implementation contains:

1. Contextual S3 investigation from existing Config/retained-scope/provider evidence.
2. Factual Agent Decision Timeline with no hidden chain-of-thought.
3. Exactly-two-account read-only Config summary code with raw account IDs hidden by default.
4. A 2–3 minute agentic SecOps demo script.
5. Regression tests preserving the existing human approval -> Gateway/Policy -> exact tool -> provider readback mutation boundary.

Credential-free regression and documentation CI passed for the implementation package. No AWS deployment, IAM/OIDC change, Gateway/Policy widening, second-account configuration or cross-account mutation is part of that code integration.

## Current next action

After PR #61 is integrated into `main`, runtime acceptance remains separate:

- activate the investigation/timeline tools only through the existing governed deployment process;
- independently verify read-only behavior and one live S3 investigation/timeline;
- configure and verify exactly two owned lab read scopes before claiming the multi-account milestone live;
- keep all cross-account mutation out of scope unless separately reviewed and approved.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
