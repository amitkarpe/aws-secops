# Agent Context

This file is compact **current-only** state for ChatGPT/coding-agent continuity.

Repository: `amitkarpe/aws-secops`

## Current product truth

- Demo v1 live acceptance remains recorded for the personal Singapore lab.
- Supported remediation families remain S3 Block Public Access and restricted SSH on retained owned demo resources.
- Approved execution remains human approval -> Gateway/Policy -> exact family tool -> provider readback.
- The model has no generic AWS mutation tool.
- The `aws_secops_operator` AgentCore Harness is the live read-only operator reasoning layer.
- Explicit `fix/apply/execute` requests do not mutate through the Harness; they remain on the separate governed human-approval path.
- Issue #60 Milestones 1–2 are live-deployed on the Harness: bounded S3 contextual investigation + factual Agent Decision Timeline.
- Milestone 3, exactly-two-account read-only SecOps, remains unclaimed until a second explicit owned read scope is configured and independently verified.

## Current operating model

> **AWS Core discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS Core independently verifies.**

ChatGPT Web is the default controller. GitHub is durable engineering state. AWS Core is the live AWS discovery/verification path. Codex is optional for deeper implementation or independent validation.

When the GitHub connector cannot start the repo's manual `workflow_dispatch`, the repo-documented fallback may be used only with explicit user authorization: trusted bootstrap of reviewed desired state followed by independent AWS verification. Do not widen the workflow trigger merely to bypass connector limitations.

## Current authority

**Issue #60 — next agentic SecOps phase**

https://github.com/amitkarpe/aws-secops/issues/60

Implementation history:
- PR #61 — contextual investigation / Decision Timeline implementation (merged)
- Issue #62 / PR #63 — provider-evidence correctness hardening (complete)
- PR #64 — Harness-native S3 investigation + Decision Timeline (merged at `2f896fe86e99c4e4096c321a40040f33daff644d`, live-deployed)
- PR #65 — unhealthy Config evidence surfaced as structured `UNVERIFIED/BLOCKED` instead of a masked Gateway error (merged at `25f835068a835ee79fd9c01adc486de82334a0ba`, live-deployed)

## Live verified Harness baseline — 2026-09-16

AWS Core independently verified after PR #65 deployment:

- CloudFormation stack `aws-secops-operator-harness`: `UPDATE_COMPLETE`;
- one `aws_secops_operator` Harness in `ap-southeast-1`, READY, version 3;
- Nova 2 Lite;
- exactly four allowed read tools:
  1. `get_config_summary`
  2. `list_config_findings`
  3. `investigate_s3_context`
  4. `get_s3_decision_timeline`
- Gateway READY with Policy mode `ENFORCE`;
- one ACTIVE Cedar policy permits exactly those four read actions;
- read Lambda IAM remains bounded to:
  - Config recorder/rule/compliance reads;
  - `GetBucketLocation`, `GetBucketTagging`, `GetBucketPublicAccessBlock`, `GetBucketPolicyStatus` on `aws-secops-bpa-*` only;
  - CloudWatch Logs writes;
- no S3 write, EC2 write, SSM, shell, generic AWS, remediation, role-chaining or cross-account mutation capability was added.

The retained S3 demo family still contains exactly 100 `aws-secops-bpa-*` buckets (`000`–`099`); sampled ownership tags match the retained demo contract.

## Current AWS Config health condition

The Config recorder is still `recording=true`, but its latest recording event is unhealthy:

- `lastStatus=FAILURE`;
- `lastStatusChangeTime=2026-09-16T03:30:25.797Z`.

This failure began before the PR #64 stack deployment started at `03:35:33Z`.

Read-only diagnosis found:
- both required Config rules remain ACTIVE;
- existing rule evaluation data remains readable;
- delivery history had a prior successful delivery;
- CloudTrail around the failure shows `AWSServiceRoleForConfig` resource-composition scans encountering unavailable/subscription-only services, including service/provider errors outside this project's two recorded resource types.

One bounded `StartConfigurationRecorder(default)` attempt made no state change. Do not stop/recreate/reconfigure the recorder or weaken the health gate merely to make the demo pass.

## Fail-closed live acceptance proof

While Config remains unhealthy:

- `investigate_s3_context` returns structured `UNVERIFIED`, `partial=true`, read-only evidence instead of a generic internal error;
- `get_s3_decision_timeline` returns all nine observable stages with `UNVERIFIED / BLOCKED / UNKNOWN / NOT_CALLED / NOT_REQUESTED` as appropriate;
- explicit `Fix this S3 compliance issue now` performs no Harness mutation and reports that evidence is unavailable and remediation remains governed;
- post-deployment Lambda logs contain `OPERATOR_READ` events with no runtime error/traceback.

Independent CloudTrail review from the first trusted-bootstrap deployment through final verification found zero:
- `PutBucketPublicAccessBlock`;
- `DeletePublicAccessBlock`;
- `PutBucketPolicy`;
- `DeleteBucketPolicy`;
- `AuthorizeSecurityGroupIngress`;
- `RevokeSecurityGroupIngress`.

## Current next actions

1. Keep the strict Config health gate. Observe/re-diagnose the recorder until a subsequent recording event becomes successful; do not broaden Config scope or bypass the gate just for the demo.
2. Once recorder health is successful, run one positive live S3 investigation + Decision Timeline acceptance. Re-arm the bounded retained demo only if a non-compliant finding is actually needed, through the existing operator-only path—not through Harness.
3. Milestone 3 remains pending: configure exactly one second explicit owned read scope, then independently prove the two-account read-only path. The current account has no AWS Organizations membership/path to reuse.
4. Keep Issue #60 open until the remaining acceptance is complete or explicitly descoped.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future scope use `ROADMAP.md`.
