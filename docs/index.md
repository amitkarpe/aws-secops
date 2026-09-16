# AWS Compliance Agent

## Governed agentic SecOps, not an autonomous AWS admin bot

This project explores a narrow question:

> How can an AI operator investigate AWS compliance evidence and help an operations team move toward a verified fix **without receiving generic AWS write access**?

The current answer deliberately uses two planes.

### Live read / investigation plane

```text
AWS Config
   ↓
aws_secops_operator AgentCore Harness
   ↓ exactly four read tools
Gateway + Policy — ENFORCE
   ↓
Bounded Config / retained-demo S3 reads
   ↓
Evidence + recommendation + Decision Timeline
```

The live Harness is read-only. `fix/apply/execute` does not give it mutation authority.

### Recorded governed mutation plane

```text
Supported exact intent
   ↓
Human Approve / Reject
   ↓
Gateway + Policy
   ↓
Exact S3 / Security Group tool
   ↓
AWS provider readback
```

The AI can investigate and recommend; it does not authorize an AWS change.

## Current verified state

| Item | Status |
|---|---|
| AgentCore Harness | **READY / live** |
| Allowed Harness tools | **4 exact read tools** |
| Gateway Policy | **ENFORCE** |
| S3 contextual investigation | **Live healthy + fail-closed paths verified** |
| Agent Decision Timeline | **Live nine-stage evidence/status view** |
| Harness mutation authority | **None** |
| Recorded Demo v1 mutation scope | **100 S3 + 10 unattached Security Groups** |
| Two-account read-only proof | **Blocked pending second authorized owned read scope** |

A Config-only `CLEAR` is intentionally narrow. If no current bounded finding exists, provider state is `NOT_READ` and risk is `NOT_ASSESSED`; the agent must not present that as provider verification.

## Start here

- [3-minute demo](operations/AGENTIC_DEMO_3_MIN.md) — shortest current operator/executive story.
- [Architecture](architecture.md) — current two-plane control path.
- [Governance](governance.md) — why the agent cannot freely change AWS.
- [Demo v1](demo-v1.md) — longer recorded remediation flow and evidence.
- [Learning path](learning-path.md) — current proof first, historical experiments second.
- [Project status](project-status.md) — concise current baseline.

## Recorded Demo v1 scope

| Item | Recorded result |
|---|---:|
| Retained demo resources | **110** |
| S3 buckets | **100** |
| Unattached Security Groups | **10** |
| Supported controls | **2** |
| Generic model-accessible AWS write tools | **0** |

The supported mutation controls remain:

- **S3 Block Public Access** — enable all four bucket-level settings on exact retained owned demo buckets.
- **Restricted SSH** — remove TCP/22 ingress from `0.0.0.0/0` on exact retained owned unattached demo Security Groups.

The current planners use complete retained-family readiness gates. This is not a general arbitrary-subset remediation engine.

## Evidence discipline

AWS Config, CloudTrail, CloudWatch and direct provider reads remain authoritative AWS evidence sources.

The Harness and Decision Timeline correlate those facts; they do not replace them or invent hidden model reasoning.

!!! note "Personal lab / POC"
    This public repository documents a personal learning/demo environment. It is not a production service and does not authorize changes to company or production infrastructure.

Issue [#60](https://github.com/amitkarpe/aws-secops/issues/60) is the current next-phase authority and contains the live acceptance record for the Harness investigation and Decision Timeline work.
