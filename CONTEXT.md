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
- Issue #60 Milestone 4 is complete: the 3-minute demo and public documentation now reflect the verified current architecture.
- Issue #60 Milestone 3 remains BLOCKED until a second explicitly authorized owned AWS read scope is available and independently verified.

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
- PR #66 — Config-only CLEAR semantics hardened so zero findings cannot be presented as provider verification (merged at `f78e680cab2154f0ff40d30084d79e5f979fbd20`, live-deployed)
- PR #67 — Milestone 4 short demo + public documentation consolidation (merged at `c798abf7b73e21c933fe0a9ee930728959f7328a`, Pages-deployed)

## Live verified Harness baseline — 2026-09-16

AWS Core independently verified after PR #66 deployment:

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
- read Lambda IAM remains bounded to:
  - Config recorder/rule/compliance reads;
  - `GetBucketLocation`, `GetBucketTagging`, `GetBucketPublicAccessBlock`, `GetBucketPolicyStatus` on `aws-secops-bpa-*` only;
  - CloudWatch Logs writes;
- no S3 write, EC2 write, SSM, shell, generic AWS, remediation, role-chaining or cross-account mutation capability was added.

The retained S3 demo family still contains exactly 100 `aws-secops-bpa-*` buckets (`000`–`099`); sampled ownership tags match the retained demo contract.

## AWS Config recovery and healthy-path acceptance

The recorder failure first observed at `2026-09-16T03:30:25.797Z` was not caused by the Harness deployment. A reversible retained-demo tag probe was not captured in Config history, proving the recorder was functionally stale rather than merely showing an old status.

Recovery used one bounded stop/start of the existing `default` recorder only:
- no recorder scope change;
- no role change;
- no Config-rule change;
- no delivery-channel change.

Observed transition:

`FAILURE -> PENDING -> SUCCESS`

Current recorder state after recovery:
- `recording=true`;
- `lastStatus=SUCCESS`;
- last successful status change: `2026-09-16T04:17:17.537Z`.

The transient tag probe restored the original bucket tags exactly and left all four S3 Block Public Access flags `true`.

Healthy-path live acceptance then proved:
- Config summary returned 107/107 S3 compliant and 15/15 restricted-SSH compliant, `partial=false`;
- S3 investigation returned Config-only CLEAR because no current retained-demo non-compliant S3 finding exists;
- Decision Timeline returned all nine observable stages;
- explicit fix request performed no Harness mutation.

## Config-only CLEAR evidence boundary

PR #66 makes zero-finding S3 investigation explicit:
- `provider_state=NOT_READ`;
- `risk_context=NOT_ASSESSED`;
- `provider_evidence=null`;
- direct S3 provider state was not read.

The Harness must not say or imply that a bucket is not public, protected, safe, secure, provider-verified or free from exposure from a Config-only CLEAR result.

The Decision Timeline shows:
- `Provider Readback = NOT_READ`;
- `Risk / Context = NOT_ASSESSED`;
when no current Config finding requires provider investigation.

## Security boundary verification

Independent verification after PR #66 found:
- Harness READY, version 4;
- exactly four allowed read tools;
- Gateway READY, Policy mode `ENFORCE`;
- Cedar policy ACTIVE for exactly those four actions;
- read Lambda IAM unchanged and read-only;
- no Lambda runtime errors during healthy-path acceptance;
- zero `PutBucketPublicAccessBlock`, `DeletePublicAccessBlock`, `PutBucketPolicy`, `DeleteBucketPolicy`, `AuthorizeSecurityGroupIngress`, or `RevokeSecurityGroupIngress` events during recovery/deployment/acceptance.

## Milestone 3 blocker

Read-only discovery found no existing second-account path that can be safely reused:
- current account is not a member of AWS Organizations;
- no cross-account `AssumeRole` activity was found in the checked 90-day CloudTrail window;
- matching local IAM roles are same-account service/GitHub/Lambda/AgentCore roles, not a reusable second-account SecOps read path;
- the current AWS Core connection exposes only the active account/session and no account/profile switch action.

No cross-account role/trust was created merely to complete the milestone.

Milestone 3 remains BLOCKED until a second explicitly authorized owned AWS read scope is provided. The first proof remains read-only; cross-account mutation is a separate later security decision.

## Milestone 4 completion

PR #67 consolidated the current public story around:

1. `docs/operations/AGENTIC_DEMO_3_MIN.md` — Capability + Evidence Discipline + Trust + Auditability;
2. `docs/architecture.md` — live read/investigation plane vs separate recorded mutation plane;
3. `docs/governance.md` — prompt intent is not authorization and Harness has no write path;
4. README / portal home / navigation / learning path / project status / roadmap — current routing and status.

Verification:
- strict MkDocs build passed on PR;
- offline regression + integration syntax passed on PR;
- post-merge strict MkDocs build passed;
- GitHub Pages deployment passed;
- post-merge offline regression + integration syntax passed.

PR #67 changed documentation only; no runtime code, IaC, IAM/OIDC, Gateway/Policy or AWS resource was changed.

## Current next actions

1. Keep Issue #60 open for Milestone 3 unless the milestone is explicitly descoped/replaced with a recorded reason.
2. When a second explicitly authorized owned AWS read scope becomes available, design the smallest exact two-account read-only proof in Git/IaC first, then independently verify account-distinguished evidence and zero mutation with AWS Core.
3. A live non-compliant S3 contextual-investigation proof is optional proportional acceptance only. If needed, re-arm one retained demo resource through an explicit operator-only path, never through the Harness, and preserve the existing governed remediation boundary.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future scope use `ROADMAP.md`.
