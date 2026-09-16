# Architecture

The design separates **reasoning**, **authorization**, **execution** and **verification**. No prompt or model response is treated as an AWS-change security boundary.

## Current architecture: two separate planes

The current system deliberately separates the live read/investigation agent from the recorded remediation executor.

### Plane A — live read / investigation

```text
AWS Config
   ↓ current compliance evidence
aws_secops_operator AgentCore Harness — Nova 2 Lite
   ↓ exactly four allowed read tools
AgentCore Gateway + Policy — ENFORCE
   ↓
Bounded read Lambda
   ├─ Config recorder/rule/compliance reads
   └─ retained-demo S3 provider reads when a current finding exists
        ↓
Evidence + recommendation + Agent Decision Timeline
```

The live Harness exposes exactly:

1. `get_config_summary`
2. `list_config_findings`
3. `investigate_s3_context`
4. `get_s3_decision_timeline`

The read Lambda has no S3 write, EC2 write, SSM, shell, generic AWS or remediation capability. The two S3 contextual tools accept no model-selected bucket/resource input.

An explicit `fix/apply/execute` request does **not** cause Plane A to mutate AWS.

### Plane B — governed mutation

The recorded Demo v1 remediation path remains separate:

```text
Supported exact remediation intent
   ↓
Server-owned retained scope / readiness
   ↓
Human Approve / Reject
   ↓
AgentCore Gateway
   ↓
AgentCore Policy
   ↓
Exact S3 or Security Group tool
   ↓
AWS API
   ↓
Direct provider readback
   ↓
Durable result

AWS Config converges independently.
```

This separation is the core trust property:

> **The agent can investigate and recommend; it does not authorize an AWS change.**

## Live read-plane control path

| Layer | Responsibility | Must not do |
|---|---|---|
| AWS Config | Supply compliance evidence | Authorize remediation |
| Harness | Interpret the operator request and choose among four exact read tools | Gain write authority from prompt intent |
| Gateway | Expose the bounded read target | Become a generic AWS proxy |
| Policy | Enforce the exact four read actions | Treat model confidence as authorization |
| Read Lambda | Perform fixed Config/S3 reads | Accept arbitrary resource selection or mutate AWS |
| Decision Timeline | Show observable evidence/status | Expose or invent hidden chain-of-thought |

### Deterministic S3 investigation scope

A live S3 provider investigation occurs only when current Config evidence contains a matching non-compliant retained-demo candidate.

```text
current Config NON_COMPLIANT S3 evidence
        +
retained demo prefix
        +
Singapore Region check
        +
exact ownership tags
        =
one bounded provider-read candidate
```

The model does not supply the bucket name.

Direct reads are limited to:

- bucket location;
- retained ownership tags;
- Block Public Access configuration;
- bucket-policy public status.

No object data is read.

## Config-only CLEAR is not provider proof

If Config returns no current retained-demo S3 non-compliant finding, the investigation stops before direct S3 provider reads.

The correct result is:

- Config result: `CLEAR`;
- `provider_state=NOT_READ`;
- `risk_context=NOT_ASSESSED`;
- `provider_evidence=null`.

That does **not** prove the bucket is non-public, safe, secure or provider-verified. It means only that no current bounded non-compliant finding was returned by AWS Config.

The Decision Timeline therefore records `Provider Readback = NOT_READ` rather than manufacturing a provider-success claim.

## Fail-closed Config health

Every bounded Config read checks the recorder health gate.

If the recorder is not recording successfully, the Harness returns structured `UNVERIFIED/BLOCKED` evidence. It does not silently use stale evidence as current truth and does not prepare a remediation conclusion.

Issue #60 live acceptance exercised this failure mode and then the recovered healthy path.

## Governed mutation boundary

Plane B preserves the recorded Demo v1 controls:

| Layer | Responsibility | Must not do |
|---|---|---|
| Server-owned planner | Intersect supported control + retained manifest + current readiness | Accept arbitrary model-selected targets |
| Human approval | Accept or reject the exact family action | Prove execution succeeded |
| Gateway | Expose the exact executor entry point | Replace Policy or IAM |
| Policy | Independently ALLOW/DENY the exact invocation | Trust a model statement as proof |
| Exact tool | Perform one narrow supported AWS change | Become generic AWS CLI/API access |
| Provider readback | Verify actual AWS state after mutation | Assume Config already converged |

Demo v1 supports two independent action families:

```text
S3 BPA            -> S3 decision -> exact S3 path
Restricted SSH    -> SG decision -> exact SG path
```

A UI may present decisions together, but that does not create blanket approval.

## Operator maintenance is separate again

Re-arming retained demo resources for a live non-compliant demonstration is an **operator-only maintenance path**. It is not a Harness tool and is not remediation approval.

Do not expose reset/re-arm to the model merely to make a demo convenient.

## Evidence hierarchy

Different sources answer different questions:

| Question | Authoritative evidence |
|---|---|
| Did an AWS API call occur? | CloudTrail |
| What did an executor/read function emit? | CloudWatch Logs |
| What does the compliance rule report? | AWS Config |
| What is the resource state now? | Direct provider readback |
| What did the workflow approve/track? | Durable workflow/batch state |
| What did Policy permit? | Gateway/Policy evidence |

The operator UI and Decision Timeline correlate evidence. They do not replace AWS sources of truth.

## Reliability and uncertainty

The design preserves explicit uncertainty:

- bounded Config reads stop at the repository-defined page/result budget;
- partial evidence remains partial;
- unhealthy Config fails closed;
- `UNKNOWN`, `UNVERIFIED`, `BLOCKED` and `FAILED` are not success;
- provider verification is required before claiming remediation completion;
- a Config-only CLEAR is never promoted into provider verification.

Historical Demo v1 recovery behavior and exact batch-state rules remain documented in [Demo v1](demo-v1.md) and the [reliability hardening proof](implementation/RELIABILITY_HARDENING_PROOF.md).

## Multi-account boundary

Issue #60 Milestone 3 requires exactly one second explicitly authorized owned AWS read scope before any two-account claim is made.

Current discovery found no reusable second-account access path. No broad cross-account role or administration trust was created to force the milestone to pass.

If a second scope is later configured, the first proof remains **read-only**. Cross-account mutation is a separate later security decision.

## Current evidence

For the fastest review:

- [3-minute demo](operations/AGENTIC_DEMO_3_MIN.md)
- [Governance](governance.md)
- [Demo v1](demo-v1.md)
- [Project status](../PROJECT_STATUS.md)
- Issue [#60](https://github.com/amitkarpe/aws-secops/issues/60)
