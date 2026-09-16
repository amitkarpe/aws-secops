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

## Issue #60 runtime acceptance checkpoint

Read-only runtime acceptance began on 2026-09-16 from `main` after PR #63.

AWS Core verified privately:

- current AWS identity and `ap-southeast-1`;
- AWS Config recorder is recording with successful status;
- both supported Config rules are currently COMPLIANT;
- current rule evaluations are 107 compliant S3 bucket evaluations and 15 compliant restricted-SSH evaluations;
- `aws-secops-operator-harness` CloudFormation stack remains `CREATE_COMPLETE`;
- the current account is not a member of AWS Organizations.

Runtime-host discovery found exactly one online SSM-managed EC2 in the connected account, but bounded read-only inspection found **no** `/opt/LibreChat`, `/opt/aws-secops`, `/opt/aws-secops-bulk`, `/opt/aws-secops-sg`, `aws-secops-bulk.service`, or `aws-secops-sg.service` on that instance.

Therefore that instance is **not** treated as the retained AWS SecOps runtime target and no deployment was attempted there.

## Current next action

Runtime activation is currently blocked on locating/reconnecting the retained AWS SecOps LibreChat/operator runtime, or explicitly designating its current host.

Once the correct runtime is reachable:

1. deploy only the merged investigation/timeline runtime delta through the existing reviewed update-code-only path;
2. independently verify `investigate_s3_context` and `get_s3_decision_timeline` remain read-only;
3. intentionally re-arm the bounded demo only through the existing operator-only path if a live non-compliant finding is needed;
4. record one live S3 investigation + Decision Timeline and provider/Config evidence;
5. do not claim the two-account milestone until a second explicit owned read scope is configured and independently verified.

The current account has no AWS Organizations membership, so there is no existing Organizations-based second-account path to reuse.

No IAM/OIDC/Gateway/Policy/Config/resource mutation was performed during this checkpoint. The only SSM action was a read-only topology command.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
