# Demo v1

Demo v1 is intentionally small enough to explain and large enough to show real batch behavior.

## Scope

- 100 retained owned empty S3 demo buckets.
- 10 retained owned unattached Security Groups.
- S3 control: bucket-level Block Public Access.
- SG control: remove unrestricted TCP/22 ingress from `0.0.0.0/0`.
- Personal Singapore lab only.

## Five-step demo flow

### 1. Show detection

Use AWS Config to show the compliance signal. Config may report resources outside the retained demo fleet; that is expected.

### 2. Show bounded demo scope

Use the Operator view to show the exact retained demo resources and whether a fresh immutable batch is ready.

Preparing the demo intentionally restores only the known demo resources to their approved non-compliant test state. **Prepare is not remediation approval.**

### 3. Ask a read-only question

Example:

```text
Show current S3 and Security Group compliance as a concise operator summary.
Use one Markdown table with status indicators. Show only totals, eligibility,
status, recommended action and next step. Do not show batch IDs or resource IDs
unless I explicitly ask. Read only; do not apply changes.
```

Expected behavior:

- current Config/planning evidence is read;
- supported families and eligible counts are summarized;
- no executor is called;
- no native approval card appears;
- no AWS mutation occurs.

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

Topic scope is an **agent instruction boundary**. AWS mutation authorization remains a separate control enforced by human approval, Gateway/Policy, exact tools and IAM.

## What the demo proves

- detection is independent of the AI;
- a read-only request remains read-only;
- the model does not receive generic AWS write access;
- human approval is explicit and family-specific;
- Policy can independently govern exact tool invocation;
- direct provider evidence, not the model's statement, determines completion;
- AWS Config can converge after provider verification.

## What the demo does not claim

- production readiness;
- multi-account remediation;
- arbitrary AWS resource support;
- WAF or other unimplemented controls;
- generic autonomous AWS administration;
- 1,000 live resources.
