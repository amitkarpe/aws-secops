# Agent Context

This file is compact **current-only** state for ChatGPT/coding-agent continuity.

Repository: `amitkarpe/aws-secops`

## Current product truth

- Demo v1 live acceptance remains recorded for the personal Singapore lab.
- Supported remediation families remain S3 Block Public Access and restricted SSH on retained owned demo resources.
- Approved execution remains human approval -> Gateway/Policy -> exact family tool -> provider readback.
- The model has no generic AWS mutation tool.
- The `aws_secops_operator` AgentCore Harness is the live read-only operator reasoning/investigation layer.
- Explicit `fix/apply/execute` requests do not mutate through the Harness; they remain on the separate governed human-approval path.
- Issue #60 Milestones 1–2 are live-deployed and healthy-path accepted: bounded S3 contextual investigation + factual Agent Decision Timeline.
- Issue #60 Milestone 4 is complete: the 3-minute demo and public documentation reflect the verified current architecture.
- Issue #60 is complete because blocked Milestone 3 has been replaced by standalone Issue #68.

## Current operating model

> **AWS Core discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS Core independently verifies.**

ChatGPT Web is the default controller. GitHub is durable engineering state. AWS Core is the live AWS discovery/verification path. Codex is optional for deeper implementation or independent validation.

When the GitHub connector cannot start the repo's manual `workflow_dispatch`, the repo-documented fallback may be used only with explicit user authorization: trusted bootstrap of reviewed desired state followed by independent AWS verification. Do not widen the workflow trigger merely to bypass connector limitations.

## Current authority

**Issue #68 — two-account read-only SecOps proof when a second owned scope is available**

https://github.com/amitkarpe/aws-secops/issues/68

Status: **BLOCKED / deferred prerequisite**. Do not create cross-account access merely to make the milestone pass.

Issue #60 remains the completed parent record for the agentic SecOps phase.

Implementation history:
- PR #61 — contextual investigation / Decision Timeline implementation (merged)
- Issue #62 / PR #63 — provider-evidence correctness hardening (complete)
- PR #64 — Harness-native S3 investigation + Decision Timeline (merged at `2f896fe86e99c4e4096c321a40040f33daff644d`, live-deployed)
- PR #65 — unhealthy Config evidence surfaced as structured `UNVERIFIED/BLOCKED` instead of a masked Gateway error (merged at `25f835068a835ee79fd9c01adc486de82334a0ba`, live-deployed)
- PR #66 — Config-only CLEAR semantics hardened so zero findings cannot be presented as provider verification (merged at `f78e680cab2154f0ff40d30084d79e5f979fbd20`, live-deployed)
- PR #67 — short demo + public documentation consolidation (merged at `c798abf7b73e21c933fe0a9ee930728959f7328a`, Pages-deployed)

## Live verified Harness baseline — 2026-09-16

AWS Core independently verified:

- CloudFormation stack `aws-secops-operator-harness`: `UPDATE_COMPLETE`;
- one `aws_secops_operator` Harness in `ap-southeast-1`, READY, version 4;
- Nova 2 Lite;
- exactly four allowed read tools:
  1. `get_config_summary`
  2. `list_config_findings`
  3. `investigate_s3_context`
  4. `get_s3_decision_timeline`
- Gateway READY with Policy mode `ENFORCE`;
- one ACTIVE Cedar policy permits exactly those four read actions;
- read Lambda IAM remains bounded to Config reads, exact retained-demo S3 read APIs, and CloudWatch Logs writes;
- no S3 write, EC2 write, SSM, shell, generic AWS, remediation, role-chaining or cross-account mutation capability was added.

The retained S3 demo family contains exactly 100 `aws-secops-bpa-*` buckets (`000`–`099`).

## Healthy-path acceptance

AWS Config recorder recovered through one bounded stop/start of the existing recorder only, with no scope/role/rule/delivery-channel change. Observed transition:

`FAILURE -> PENDING -> SUCCESS`

Healthy-path live acceptance proved:
- Config summary: 107/107 S3 compliant and 15/15 restricted-SSH compliant, `partial=false`;
- S3 investigation: Config-only CLEAR because no current retained-demo non-compliant S3 finding exists;
- Decision Timeline: all nine observable stages;
- explicit fix request: no Harness mutation.

PR #66 makes zero-finding S3 investigation explicit:
- `provider_state=NOT_READ`;
- `risk_context=NOT_ASSESSED`;
- `provider_evidence=null`.

A Config-only CLEAR must never be presented as proof that a bucket is safe, non-public, protected or provider-verified.

## Security boundary verification

Independent verification found:
- Harness READY, version 4;
- exactly four allowed read tools;
- Gateway READY, Policy mode `ENFORCE`;
- Cedar policy ACTIVE for exactly those four actions;
- read Lambda IAM unchanged and read-only;
- no Lambda runtime errors during healthy-path acceptance;
- zero S3 BPA/policy or SG-ingress mutation events during recovery/deployment/acceptance.

## Issue #68 prerequisite blocker

Read-only discovery found no existing second-account path that can be safely reused:
- current account is not a member of AWS Organizations;
- no cross-account `AssumeRole` activity was found in the checked 90-day CloudTrail window;
- matching local IAM roles are same-account service/GitHub/Lambda/AgentCore roles, not a reusable second-account SecOps read path;
- the current AWS Core connection exposes only the active account/session and no account/profile switch action.

No cross-account role/trust was created merely to complete the proof.

Start Issue #68 only when a second explicitly authorized owned AWS read scope is provided. The first proof remains read-only; cross-account mutation is a separate later security decision.

## Current next actions

1. Do not implement Issue #68 until its explicit second-account prerequisite exists.
2. When it exists, design the smallest exact two-account read-only proof in Git/IaC first, then independently verify account-distinguished evidence and zero mutation with AWS Core.
3. If new unblocked product work is desired before then, create a separate standalone Issue from `ROADMAP.md`; do not mix it into Issue #68.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future scope use `ROADMAP.md`.
