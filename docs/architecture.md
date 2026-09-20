# Architecture

The design separates **evidence**, **reasoning**, **authorization**, **execution** and **verification**.

No prompt or model response is an AWS-change security boundary.

## Plane A — Compliance Agent v1 reasoning path

```text
Organization / account Config evidence
        ↓
unified Config backend (:1111)
        ↓
strict Compliance Agent v1 adapter
        ↓
dedicated AgentCore Harness
        ↓
Nova 2 Lite, no Harness tools
        ↓
one read-only MCP result
        ↓
LibreChat
```

Scope:

- `lab-dev`
- `lab-poc`
- `lab-qa`
- `lab-sec`

Controls:

- `s3-bucket-level-public-access-prohibited`
- `restricted-ssh`

The adapter fails closed unless the exact 4-account × 2-control matrix is present.

Compliance Agent v1 can:

- report current status;
- explain supported findings;
- produce a no-change remediation plan;
- return identifiers only when authorized evidence contains them.

For explicit fix intent, the same LibreChat agent may leave this reasoning plane and invoke the bounded execution plane below.

## Plane B — Compliance Agent v1 governed mutation path

```text
explicit fix intent
        ↓
server-owned frozen batch
        ↓
native Approve / Reject
        ↓
fixed CodeBuild project / existing G/O controller
        ↓
exact registered target sessions
        ↓
exact S3 or EC2 action
        ↓
direct provider readback
        ↓
AWS Config converges independently
```

This path is bounded to the existing four LAB aliases and two controls. It is now part of Compliance Agent v1's shell tool set, but native human approval remains the authorization boundary and the Harness itself receives no mutation tool.

## Plane C — historical / retained experiments

Earlier `aws_secops_operator`, Gateway/Policy, 100-S3 and 10-SG flows remain useful engineering evidence.

They are retained as historical or supporting proof, not the primary current Compliance Agent v1 runtime.

## Evidence hierarchy

| Question | Authoritative evidence |
|---|---|
| What does Config report? | AWS Config / unified Config backend |
| Did the exact resource change? | Direct S3 / EC2 provider readback |
| What exact batch was approved/rejected? | Durable approval/execution state |
| Did an AWS API call occur? | CloudTrail |
| What did runtime code emit? | CloudWatch / service logs |
| What did the v1 agent say? | LibreChat / AgentCore Harness response |

## Current web surfaces

- Config Dashboard: `config.astromedicomp.org`
- LibreChat / Compliance Agent v1: `sec.astromedicomp.org`
- `ops.astromedicomp.org`: redirect/legacy entry point

## Safety boundary

- Personal LAB only.
- Exactly four approved aliases and two controls for v1.
- No Config automatic remediation.
- No generic model-accessible AWS admin tool.
- Provider readback proves remediation completion.
- Config is independent asynchronous evidence.
- `UNKNOWN`, partial, failed or unavailable evidence is not success.
