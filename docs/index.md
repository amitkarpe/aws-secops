# AWS Compliance Agent

## Governed remediation, not an autonomous AWS admin bot

This project explores a narrow question:

> How can an AI assistant help operations teams move from an AWS compliance finding to a verified fix **without receiving generic AWS write access**?

Demo v1 proves one bounded answer:

```text
AWS Config
   ↓ Detect
AWS Compliance Agent
   ↓ Explain + plan
Human Approve / Reject
   ↓ Authorize exact intent
AgentCore Gateway + Policy
   ↓ Govern
Exact remediation tool
   ↓ Execute
AWS provider readback
   ↓ Verify
AWS Config convergence
```

## Recorded Demo v1 scope

| Item | Result |
|---|---:|
| Retained demo resources | **110** |
| S3 buckets | **100** |
| Unattached Security Groups | **10** |
| Supported controls | **2** |
| Generic model-accessible AWS write tools | **0** |

The two supported controls are:

- **S3 Block Public Access** — enable all four bucket-level settings on exact retained owned demo buckets.
- **Restricted SSH** — remove TCP/22 ingress from `0.0.0.0/0` on exact retained owned unattached demo Security Groups.

The current planners use complete retained-family readiness gates. This is not a general arbitrary-subset remediation engine.

## What the AI contributes

The model explains current evidence, summarizes findings and maps an explicit operator request onto supported workflows. Deterministic code owns the controls, manifests, exact action, batch state and verification. Human approval and Gateway/Policy remain separate from model reasoning.

## Start here

- [Architecture](architecture.md) — the current native Bedrock/LibreChat control path and operator-maintenance branch.
- [Demo v1](demo-v1.md) — current prompts, evidence digest, limitations and end-to-end story.
- [Governance](governance.md) — trust assumptions and the separation between model, human approval, Policy, exact tools and evidence.
- [Learning path](learning-path.md) — current proof first, historical experiments second.
- [Project status](project-status.md) — concise current baseline.

## Important boundaries

!!! note "Personal lab / POC"
    This public repository documents a personal learning/demo environment. It is not a production service and does not authorize changes to company or production infrastructure.

AWS Config, CloudTrail, CloudWatch and direct provider reads remain authoritative AWS evidence sources. The agent and Operator UI coordinate and explain workflow state; they do not replace those services.

Earlier Harness and multi-source pilot pages remain available as dated research/history. They are not the current primary Demo v1 architecture.
