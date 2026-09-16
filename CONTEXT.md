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
- PR #64 is merged and moves Issue #60 Milestones 1–2 onto the existing read-only AgentCore Harness so they no longer depend on the retired WSL/LibreChat runtime topology.

## Current operating model

> **AWS Core discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS Core independently verifies.**

ChatGPT Web is the default controller. GitHub is durable engineering state. AWS MCP/Core is the live AWS discovery and verification path. Codex is used only when deeper implementation or independent runtime validation materially helps.

## Verified baseline

- one `aws_secops_operator` Harness in `ap-southeast-1`;
- Nova 2 Lite;
- currently deployed Harness still has the original two read-only AWS Config tools until PR #64 is deployed;
- Gateway Policy mode `ENFORCE`;
- current deployed read Lambda has Config/log reads only and no S3/EC2/SSM mutation authority;
- live Config summary + focused findings reads passed for both supported controls;
- negative `fix/apply/execute` boundary passed;
- Demo v1 mutation path remains separate and governed.

## Current authority

**Issue #60 — next agentic SecOps phase**

https://github.com/amitkarpe/aws-secops/issues/60

Implementation history:
- PR #61 — contextual investigation / Decision Timeline implementation (merged)
- Issue #62 / PR #63 — post-merge provider-evidence correctness hardening (complete)
- PR #64 — Harness-native S3 investigation + Decision Timeline (merged at `2f896fe86e99c4e4096c321a40040f33daff644d`)

## Runtime discovery and design correction

Read-only runtime acceptance on 2026-09-16 established:

- current AWS identity and `ap-southeast-1` verified privately;
- AWS Config recorder is healthy;
- both supported Config rules are currently COMPLIANT;
- current rule evaluations observed 107 compliant S3 bucket evaluations and 15 compliant restricted-SSH evaluations;
- `aws-secops-operator-harness` CloudFormation stack is `CREATE_COMPLETE`;
- current account is not a member of AWS Organizations;
- exactly 100 retained `aws-secops-bpa-*` demo buckets still exist (`000`–`099`); sampled ownership tags match the historical `owner=amit`, `phase=bulk-bpa`, `project=aws-secops`, `environment=dev`, `version=r01` contract;
- all-region SSM discovery found only one managed EC2 in this account, belonging to the separate Security Copilot / `agentic-ai-cybersecurity-lab` project, with no AWS SecOps runtime present.

Repository history clarified the old UI topology:
- named UI / Nginx / LibreChat ran on a retained personal-lab EC2 using `AWS_PROFILE=amit`;
- the bulk/Config writer used a separate `vagent` lane from a local WSL/operator workstation and required that workstation to be up;
- the current AWS Core connection is the `vagent` lab, not the historical `amit` UI host.

Therefore Issue #60 Milestones 1–2 no longer require recovering that old split runtime. PR #64 extends the existing `aws_secops_operator` Harness instead.

## PR #64 trusted scope

After deployment the existing Harness should expose exactly four read tools:

1. `get_config_summary`
2. `list_config_findings`
3. `investigate_s3_context`
4. `get_s3_decision_timeline`

The two new tools:
- accept no model-selected bucket/resource input;
- derive a deterministic candidate only from current Config NON_COMPLIANT S3 evidence;
- require prefix `aws-secops-bpa-*`, Singapore Region, and exact retained ownership tags before direct S3 reads;
- add only `GetBucketLocation`, `GetBucketTagging`, `GetBucketPublicAccessBlock`, and `GetBucketPolicyStatus` on the retained S3 prefix;
- add no S3 write, EC2 write, SSM, shell, generic AWS, remediation or cross-account capability;
- expose an observable evidence/status timeline, not hidden chain-of-thought.

Latest-head PR #64 offline regression + integration JavaScript syntax checks passed before squash merge.

## Current next action

Deploy merged PR #64 through the existing manual main-only **AWS operator Harness deploy** GitHub Actions workflow, then use AWS Core to independently verify:

1. stack update completed cleanly;
2. Harness exposes exactly the four expected read tools;
3. `investigate_s3_context` returns a truthful read-only result for current provider/Config state;
4. `get_s3_decision_timeline` returns the factual nine-stage status timeline;
5. explicit `fix/apply/execute` still performs no Harness mutation and points to the separate governed human-approval path.

The current ChatGPT GitHub connector can review/merge workflow-backed code but does not expose a `workflow_dispatch` action, so starting this manual deployment requires the existing GitHub Actions UI (or another authorized workflow-dispatch client). Do not replace the workflow with a broader automatic trigger merely to bypass that limitation.

A live non-compliant S3 investigation is a later proportional acceptance step. If needed, re-arm only the bounded retained demo through an explicit operator-only path after the read-only Harness deployment is verified. Do not expose reset/re-arm to the Harness.

Milestone 3 remains unclaimed until a second explicit owned read scope is configured and independently verified. The current account has no AWS Organizations membership, so there is no existing Organizations-based second-account path to reuse.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
