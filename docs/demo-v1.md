# Demo v1

Demo v1 is intentionally small enough to explain and large enough to show real batch behavior.

## Scope

- 100 retained owned empty S3 demo buckets.
- 10 retained owned unattached Security Groups.
- S3 control: bucket-level Block Public Access.
- SG control: remove unrestricted TCP/22 ingress from `0.0.0.0/0`.
- Personal Singapore lab only.
- Current planning is family-complete: the whole retained S3 or SG family must pass the current readiness and eligibility gates before that family's remediation batch is prepared. Demo v1 is not a general arbitrary-subset engine.

## Five-step demo flow

### 1. Show detection

Use AWS Config to show the compliance signal. Config may report resources outside the retained demo fleet; that is expected.

### 2. Show bounded demo scope

Use the Operator view to show the exact retained demo resources and whether a fresh immutable batch is ready.

Preparing the demo intentionally restores only the known demo resources to their approved non-compliant test state. **Prepare is not remediation approval.** It is a separate operator maintenance path and is not exposed as an agent reset tool.

### 3. Ask a read-only question

```text
Show current S3 and Security Group compliance as a concise operator summary.
Use one Markdown table with status indicators. Show only totals, eligibility,
status, recommended action and next step. Do not show batch IDs or resource IDs
unless I explicitly ask. Read only; do not apply changes.
```

Expected behavior in the recorded demo:

- current Config/planning evidence is read;
- supported families and eligible counts are summarized;
- no executor is called;
- no native approval card appears;
- no AWS mutation occurs.

The read-only/execution distinction is an agent-behavior rule plus tested behavior; it is not the hard AWS authorization boundary. Human approval, Gateway/Policy, exact tools and IAM remain separate controls.

### 4. Explicitly request remediation

```text
Fix all currently eligible demo compliance findings.
```

Expected behavior:

- the server determines eligible families and exact retained scope;
- S3 and SG are prepared as independent action families;
- native Approve/Reject decisions are shown separately;
- approval does not bypass Gateway/Policy;
- exact tools execute only after the corresponding decision and independent governance checks.

### 5. Read progress and final evidence

```text
Show current S3 and Security Group remediation status as a concise operator dashboard.
Use one Markdown table with status indicators. Show totals, completed, running,
pending, failed and unknown. Hide batch IDs and resource IDs unless I ask for details.
```

A useful mid-run result looks like:

| Control | Completed | Running | Pending | Failed | Unknown |
|---|---:|---:|---:|---:|---:|
| S3 BPA | 45 | 3 | 52 | 0 | 0 |
| Restricted SSH | 10 | 0 | 0 | 0 | 0 |

The final result should show all supported demo resources provider-verified with failed/unknown outcomes explicitly visible.

## Specialist scope guardrail

The AWS Compliance Agent is intentionally limited to AWS compliance operations. Clearly unrelated general-assistant requests should be rejected as out of scope with no compliance tools invoked.

Topic scope is an agent instruction boundary. AWS mutation authorization remains a separate control enforced by human approval, Gateway/Policy, exact tools and IAM.

## Current evidence digest

| Milestone | What it supports | Evidence |
|---|---|---|
| Governed S3 execution | Native human decision, Gateway/Policy path, exact bounded S3 tool, provider readback and durable batch behavior | [PR #23](https://github.com/amitkarpe/aws-secops/pull/23) and [S3 execution proof](implementation/PLATFORM_PHASE11_13_PROOF.md) |
| Unified Config + SG direction | AWS Config evidence, exact restricted-SSH family and unified AWS Compliance Agent direction | [PR #25](https://github.com/amitkarpe/aws-secops/pull/25) |
| Demo v1 acceptance | Config-driven planning, separate S3/SG approvals, repeatable Operator flow and recorded 100-S3 + 10-SG end-to-end acceptance | [PR #27](https://github.com/amitkarpe/aws-secops/pull/27) |

The accepted PR #27 record reported the retained 100 S3 + 10 SG demo exercised end to end and a 101-test repository baseline at that point. This page does not claim that every historical AWS proof was rerun after later documentation-only changes.

## Evidence source nuance

- S3 Operator status is primarily saved durable batch/provider-verification evidence; a UI refresh should not be described as a fresh full S3 provider scan.
- SG status includes current provider reads.
- AWS Config remains independent asynchronous evidence for both families.
- CloudTrail, CloudWatch, Config and provider reads remain authoritative for their respective questions; the Operator view correlates workflow state rather than replacing them.

## What the demo proves

- detection is independent of the AI;
- tested read-only requests produced no approval/execution;
- the model does not receive a generic AWS write tool;
- human approval is explicit and family-specific;
- Policy can independently govern exact tool invocation;
- direct provider evidence, not the model's statement, determines completion;
- AWS Config can converge after provider verification;
- exact current scope is server-owned rather than model-selected.

## What the demo does not claim

- production readiness;
- multi-account remediation;
- arbitrary AWS resource or arbitrary-subset remediation support;
- WAF or other unimplemented controls;
- generic autonomous AWS administration;
- 1,000 live resources;
- proof that a specific human identity is part of the Policy decision;
- complete least-privilege certification of every permission on the retained host.

## Known reliability limit

Issue #32 hardens SG interruption handling using safe terminalization and read-only reconciliation, not automatic continuation. The recovery section below distinguishes the offline-tested correction from the recorded live demo; production recovery is not claimed.

## Recovery and status hardening (Issue #32)

The existing successful live demo remains the acceptance baseline. The following corrections have offline regression coverage; deployment/live validation is separate.

| Situation | Honest result |
|---|---|
| Config reaches its 10-page or 250-result budget | Partial evidence; no ready-to-prepare claim |
| Config returns a repeated or invalid token | Read fails; existing provider/batch counts remain separate |
| SG process stops with work in flight | Claimed work becomes UNKNOWN; unstarted approvals expire as FAILED / not dispatched |
| SG worker cannot start | No dispatch; old approval consumed; new preview/approval required |
| Reconciliation during execution | Refused until in-flight work stops |
| Old S3 journal without verification time | Counts retained; time is not recorded |
| S3 card refresh | Saved readback result, not a new AWS scan |

There is no new **Resume all** or arbitrary-subset operation. After read-only reconciliation, the existing owner-operated preview path may create a fresh full-manifest batch, preserving history and requiring new approval. The normal Config planner's whole-family gates still apply; do not reset the fleet or edit a journal to force readiness.

See [the reproducible hardening evidence](implementation/RELIABILITY_HARDENING_PROOF.md) for exact coverage and limits.
