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

## Current operating model

> **AWS Core discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS Core independently verifies.**

ChatGPT Web is the default controller. GitHub is durable engineering state. AWS MCP/Core is the live AWS discovery and verification path. Codex is used only when deeper implementation or independent runtime validation materially helps.

## Completed milestone

Issues #44, #49, and #55 are completed.

Verified outcome:

- one `aws_secops_operator` Harness in `ap-southeast-1`;
- Nova 2 Lite;
- exact two read-only AWS Config tools through AgentCore Gateway;
- Gateway ready with Policy mode `ENFORCE`;
- Policy engine/operator policy active;
- read Lambda present with no S3/EC2/SSM mutation authority;
- live Config summary + focused findings reads passed for both supported controls;
- negative `fix/apply/execute` boundary passed;
- Demo v1 mutation: **NO**.

PR #56 is a completed Codex verification handoff artifact. No further verification is required for this milestone.

## Current authority

No active implementation milestone is selected yet.

## Current next action

Select one new product milestone from `ROADMAP.md`. Preferred next step is operator-summary polish on the deployed Harness: concise operator answers, consistent Markdown tables, minimal identifiers by default, and no change to the existing AWS authorization/remediation boundary.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
