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
- PR #61 merged the Issue #60 contextual-investigation / Decision Timeline implementation.
- Post-merge correctness Issue #62 is complete via PR #63.

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

Correctness hardening: **Issue #62 / PR #63** (complete).

## Issue #62 verified correction

PR #63 corrected the investigation semantics before live activation:

1. whole durable S3 batch is aggregated in bounded pages;
2. `before` is preview/precondition evidence only;
3. terminal `COMPLETED` / `SKIPPED` `after` values are provider remediation truth;
4. mixed/partial/unknown states block fleet-wide remediation conclusions;
5. batch pagination rejects a changing batch snapshot;
6. two-account reads are hard-allowlisted to STS identity + Config compliance summary only;
7. IAM least-privilege remains a separate runtime verification claim.

Credential-free offline regression and integration syntax checks passed before squash merge.

## Current next action

Runtime acceptance remains under Issue #60:

- activate the investigation/timeline tools only through the existing governed deployment process;
- independently verify read-only behavior and one live S3 investigation/timeline;
- configure and verify exactly two owned lab read scopes before claiming the multi-account milestone live;
- keep all cross-account mutation out of scope unless separately reviewed and approved.

No AWS deployment, IAM/OIDC/Gateway/Policy change, or cross-account mutation was part of Issue #62.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
