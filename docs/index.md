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

## Proven Demo v1 scope

| Item | Result |
|---|---:|
| Retained demo resources | **110** |
| S3 buckets | **100** |
| Unattached Security Groups | **10** |
| Supported controls | **2** |
| Generic AWS write tools exposed to the model | **0** |

The two supported controls are:

- **S3 Block Public Access** — enable all four bucket-level settings on exact retained owned demo buckets.
- **Restricted SSH** — remove TCP/22 ingress from `0.0.0.0/0` on exact retained owned unattached demo Security Groups.

## What to read next

- [Architecture](architecture.md) — what each layer does.
- [Demo v1](demo-v1.md) — safe end-to-end demo prompts and expected behavior.
- [Governance](governance.md) — why approval, Policy and provider readback are separate controls.
- [Learning path](learning-path.md) — a guided tour through deeper proofs and runbooks.
- [Operations Console direction](operator-console.md) — how the current demo/operator UI can evolve for long-term support.

## Important boundaries

!!! note "Personal lab / POC"
    This public repository documents a personal learning/demo environment. It is not a production service and does not authorize changes to company, GovTech or production infrastructure.

AWS Config, CloudTrail, CloudWatch and direct provider reads remain authoritative AWS evidence sources. The agent and Operator UI coordinate and explain workflow state; they do not replace those services.
