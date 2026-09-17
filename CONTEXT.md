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
- Issue #60 is complete: bounded S3 contextual investigation, factual Agent Decision Timeline, short demo and documentation are live/accepted; its multi-account milestone moved to Issue #68.
- Issue #70 is complete: the existing S3 investigation now has bounded CloudTrail Event History attribution for a deterministic retained-owned candidate, with no new Harness tool or mutation authority.
- Issue #68 is now **ACTIVE**: the `management-lab` prerequisite passed on 2026-09-17 and the project contract now permits a broad read-only hub/spoke role for personal LAB/DEV accounts.

## Current operating model

> **AWS Core discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS Core independently verifies.**

ChatGPT Web is the default controller. GitHub is durable engineering state. AWS Core is the live AWS discovery/verification path. Codex is used when a bundled implementation materially needs local/profile/runtime access or deeper engineering; do not hand X isolated one-command checks that G can perform directly.

For personal LAB/DEV multi-account discovery, demonstration velocity is preferred over repeated micro-tuning of read permissions. Broad read-only cross-account access is intentional; broad mutation is not.

Preferred topology:

```text
ChatGPT / AWS Core
       |
       v
active SecOps hub account
       |
       +-- AssumeRole -> registered LAB/DEV account A broad read-only
       +-- AssumeRole -> management-lab broad read-only
       +-- AssumeRole -> later registered account C/D broad read-only
```

When the GitHub connector cannot start the repo's manual `workflow_dispatch`, the repo-documented fallback may be used only with explicit user authorization: trusted bootstrap of reviewed desired state followed by independent AWS verification. Do not widen the workflow trigger merely to bypass connector limitations.

## Current authority

**Issue #68 — multi-account read-only SecOps proof: 2-account gate -> 3-4 account demo**

https://github.com/amitkarpe/aws-secops/issues/68

Status: **ACTIVE**.

Prerequisite evidence already passed:
- private AWS Platform `management-lab` Environment exists;
- local AWS CLI profile hint `amit` passed expected account-identity and `ap-southeast-1` Region equality checks;
- no AWS resource, IAM, OIDC, remediation or workload change was made by that bootstrap.

Current contract:
- start with a 2-account technical acceptance gate;
- use one ChatGPT/AWS-MCP-visible hub account plus a reusable broad read-only spoke role;
- allow broad read/list/get/describe-style discovery needed for resource, IAM/policy, compliance and audit visibility;
- keep representative mutation APIs denied through the read role;
- after the 2-account gate passes, scale the same pattern to 3-4 explicitly registered owned LAB/DEV accounts;
- cross-account remediation remains a separate later milestone/role.

Completed recent authority:
- Issue #60 — completed parent agentic SecOps phase.
- Issue #70 — completed bounded recent-change attribution milestone.

Implementation history:
- PR #61 — contextual investigation / Decision Timeline implementation (merged)
- Issue #62 / PR #63 — provider-evidence correctness hardening (complete)
- PR #64 — Harness-native S3 investigation + Decision Timeline (live-deployed)
- PR #65 — unhealthy Config evidence surfaced as structured `UNVERIFIED/BLOCKED` (live-deployed)
- PR #66 — Config-only CLEAR semantics hardened (live-deployed)
- PR #67 — short demo + public documentation consolidation (Pages-deployed)
- PR #69 — Issue #60 closure / Issue #68 governance update
- PR #71 — bounded CloudTrail recent-change attribution (live-deployed)
- PR #72 — Config-only CLEAR risk/exposure wording hardening (live-deployed)

## Live verified Harness baseline — 2026-09-16

AWS Core independently verified after Issue #70:

- CloudFormation stack `aws-secops-operator-harness`: `UPDATE_COMPLETE`;
- one `aws_secops_operator` Harness in `ap-southeast-1`, READY, version 6;
- Nova 2 Lite;
- exactly four allowed read tools:
  1. `get_config_summary`
  2. `list_config_findings`
  3. `investigate_s3_context`
  4. `get_s3_decision_timeline`
- Gateway READY with Policy mode `ENFORCE`;
- one ACTIVE Cedar policy permits exactly those four read actions;
- read Lambda IAM remains bounded to Config reads, exact retained-demo S3 read APIs, Region-bound `cloudtrail:LookupEvents`, and CloudWatch Logs writes;
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

Config-only CLEAR semantics are explicit:
- `provider_state=NOT_READ`;
- `risk_context=NOT_ASSESSED`;
- `provider_evidence=null`;
- `evidence_boundary=Config-only CLEAR does not establish current provider state or absence of exposure/risk`;
- confidence is scoped only to the AWS Config observation.

A Config-only CLEAR must never be presented as proof that a bucket is safe, non-public, protected, provider-verified or free from exposure/risk.

## Issue #70 acceptance

Bounded recent-change attribution is live and accepted.

Verified behavior:
- no new Harness tool or arbitrary resource selector;
- CloudTrail Event History is queried only for the deterministic retained-owned S3 candidate when one exists;
- output is capped to five relevant events and exposes action/time only, with identity suppressed by default;
- when no current bounded finding exists, provider state and CloudTrail history are honestly `NOT_READ` / `NOT_EVALUATED`;
- live Decision Timeline reports `Risk / Context = NOT_ASSESSED` for Config-only CLEAR;
- live `Fix this S3 compliance issue` request invoked only the four read tools and did not invoke any executor;
- representative AWS mutation APIs remained denied;
- final CloudTrail audit showed zero S3/SG/SSM mutation events.

## Issue #68 current next actions

1. Define the reusable hub/spoke **broad read-only** role contract in Git/IaC, using the actual AWS Core hub identity discovered by STS at runtime rather than hard-coding private account IDs here.
2. Prove the first 2-account path end-to-end: hub identity -> AssumeRole -> account-distinguished inventory/security evidence -> zero mutation.
3. After that gate passes, register/reuse the same role contract for 1-2 more owned LAB/DEV accounts and present a 3-4 account security overview for the stakeholder demo.
4. Keep cross-account remediation out of this role. If needed later, create a separate demo automation/remediation role and milestone.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future scope use `ROADMAP.md`.
