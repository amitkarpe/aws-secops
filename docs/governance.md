# Governance

The central design rule is:

> **The model is an assistant, not the authorization boundary.**

The current design makes that visible by separating the live read/investigation plane from the governed mutation plane.

## 1. Two governance planes

### Live Harness: read / investigate only

The `aws_secops_operator` AgentCore Harness can use exactly four bounded read tools for the two supported Config controls and retained-demo S3 context.

It has no model-accessible AWS write, shell, generic AWS, arbitrary resource-selection or remediation tool.

An operator saying `fix`, `apply` or `execute` does not change that authority. The Harness remains read-only and points to the separate governed remediation path.

### Recorded Demo v1: governed mutation

Actual AWS mutation remains:

`server-owned scope -> human approval -> Gateway/Policy -> exact tool -> provider readback`

Recommendation, approval, Policy ALLOW and provider success are distinct facts.

## 2. Topic and intent are not hard authorization

Agent instructions keep the AWS Compliance Agent focused on AWS compliance/security operations and help distinguish read-only questions from execution intent.

Those instructions improve behavior, but **prompt intent is not the AWS security boundary**.

For the live Harness, even an explicit execution request still has no mutation tool to call. For the recorded mutation path, AWS changes additionally require deterministic scope, human approval, Gateway/Policy and exact executor permissions.

## 3. Read scope is deterministic

The Harness does not accept arbitrary AWS targets.

Current read scope is fixed to:

- the two supported AWS Config controls;
- bounded Config result pagination;
- retained-demo S3 resources matching the expected prefix, Region and ownership tags;
- four direct S3 read APIs only when a current bounded S3 finding requires investigation.

The model cannot supply a bucket name to expand the investigation target.

## 4. Evidence claims are bounded

The agent may explain only what the evidence supports.

Examples:

- Config says `NON_COMPLIANT` → this is a Config finding, not proof of sensitive-data exposure or attacker activity.
- Config returns no current bounded finding → `CLEAR` is Config evidence only.
- If direct S3 provider state was not read → report `provider_state=NOT_READ` and `risk_context=NOT_ASSESSED`.
- Provider readback may support a provider-state statement only when the bounded provider read actually occurred.

The Harness must not turn Config-only `CLEAR` into “safe”, “not public”, “provider verified” or equivalent language.

## 5. Fail closed on unhealthy evidence

The read path checks AWS Config recorder health before treating current Config evidence as usable.

If that health gate fails:

- result is `UNVERIFIED/BLOCKED`;
- no provider/remediation conclusion is invented;
- the Decision Timeline shows which stages were not called;
- no mutation occurs.

This behavior was exercised live during Issue #60 before the recorder was recovered.

## 6. Server-owned mutation scope

For the recorded Demo v1 mutation path, deterministic server code owns:

- supported controls;
- retained resource manifests;
- eligible resource intersection;
- exact remediation action;
- immutable batch identity and approval data.

A caller/model-supplied resource ID is not enough to expand the blast radius.

Demo v1 uses conservative family-complete readiness gates rather than arbitrary model-selected subsets.

## 7. Human approval

S3 and Security Group changes remain independently approved.

```text
S3 request -> Approve / Reject
SG request -> Approve / Reject
```

Approval means only:

> **This exact supported request may proceed to the next governance layer.**

It does not prove the AWS change happened or succeeded.

## 8. Gateway + Policy

Gateway exposes bounded tool entry points. Policy independently evaluates the exact permitted action.

The separation is intentional:

- model recommendation is not authorization;
- human approval is not Policy ALLOW;
- Policy ALLOW is not provider success;
- Config compliance is not provider readback.

For the live Harness, Gateway Policy is `ENFORCE` and the active policy permits exactly the four read actions.

## 9. Exact tools and IAM

The current read Lambda is bounded to:

- Config recorder/rule/compliance reads;
- `GetBucketLocation`;
- `GetBucketTagging`;
- `GetBucketPublicAccessBlock`;
- `GetBucketPolicyStatus`;
- CloudWatch Logs writes.

The retained S3 read permissions are prefix-bounded. The Harness receives no S3 write, EC2 write, SSM or generic AWS action.

The recorded mutation plane uses separate exact tools for the supported S3 BPA and restricted-SSH actions.

## 10. Provider verification

After a governed mutation, AWS is read again.

A remediation may be reported completed only when direct provider state matches the approved target. `FAILED` and `UNKNOWN` remain explicit outcomes.

AWS Config is independent asynchronous evidence and may converge later.

## 11. Operator maintenance is separate

`Prepare demo` / reset / re-arm is privileged operator maintenance for retained lab resources.

It is:

- not a Harness tool;
- not normal remediation approval;
- not evidence that the model can reset AWS;
- not something to expose merely to simplify a demo.

## 12. Multi-account remains read-only-first

Issue #60 Milestone 3 requires a second explicitly authorized owned AWS read scope.

Current discovery found no reusable second-account path. No broad cross-account role, Organizations trust or admin capability was created just to satisfy the milestone.

If a second scope is later configured, the first proof remains read-only. Cross-account mutation requires a separate design/review decision.

## Evidence sources

| Question | Authoritative evidence |
|---|---|
| Did an AWS API call happen? | CloudTrail |
| What did the read/executor function log? | CloudWatch Logs |
| What does the compliance rule report? | AWS Config |
| What is the resource state now? | Direct provider readback |
| What did the workflow approve/track? | Durable batch/approval state |
| What did Policy decide? | Gateway/Policy evidence |

The Decision Timeline and any future Operations Console should correlate these sources, not replace them.

## Trust and limits

This remains a personal-lab POC. It does not claim:

- production identity governance;
- hostile multi-tenant isolation;
- arbitrary-resource remediation;
- generic autonomous AWS administration;
- live multi-account proof without a second configured account;
- that a Config finding alone proves business impact or exploitability.

For the shortest current walkthrough, use the [3-minute demo](operations/AGENTIC_DEMO_3_MIN.md). For the recorded mutation proof, use [Demo v1](demo-v1.md).

## Public safety

This repository is public. Never publish credentials, account IDs, private ARNs/endpoints, auth material, session IDs, raw private findings or private screenshots.
