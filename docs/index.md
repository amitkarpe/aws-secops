# AWS Compliance Agent

## Governed agentic SecOps, not an autonomous AWS admin bot

This project explores one narrow question:

> How can an AI operator use AWS compliance evidence to explain and plan a safe fix **without receiving generic AWS write access**?

## Current clean read path

```text
AWS Config / unified Config backend
        ↓
Compliance Agent v1 MCP
        ↓
dedicated AgentCore Harness
        ↓
Nova 2 Lite reasoning
        ↓
read-only LibreChat answer
```

Compliance Agent v1 exposes exactly one MCP tool and the Harness itself has no tools.

## Separate governed mutation path

```text
explicit supported fix intent
        ↓
frozen exact four-account batch
        ↓
native Approve / Reject
        ↓
fixed CodeBuild + existing G/O controller
        ↓
exact supported AWS action
        ↓
provider readback
        ↓
independent AWS Config convergence
```

The clean v1 agent does not inherit this execution authority.

## Current verified state

| Item | Status |
|---|---|
| Four-account Config evidence | **LIVE — 4 aliases × 2 controls** |
| Compliance Agent v1 | **LIVE / read-only** |
| AgentCore Harness | **PASS — dedicated v1 Harness** |
| Harness tools | **0** |
| MCP tools exposed by v1 | **1 — ask_compliance_agent_v1** |
| Golden prompts | **PASS 5/5** |
| Authenticated LibreChat smoke | **PASS** |
| Governed four-account remediation proof | **PASS — separate bounded path** |
| Generic model-accessible AWS admin | **None** |
| GitHub Release `compliance-agent-v1.0.0` | **Pending** |

Latest clean v1 live acceptance: **2026-09-20**.

## Start here

- [3-minute demo](operations/AGENTIC_DEMO_3_MIN.md)
- [Architecture](architecture.md)
- [Governance](governance.md)
- [Learning path](learning-path.md)
- [Project status](project-status.md)
- [Compliance Agent v1 source](https://github.com/amitkarpe/aws-secops/tree/main/agents/compliance-agent-v1)

## Evidence discipline

AWS Config, CloudTrail, CloudWatch and direct provider reads remain authoritative AWS evidence sources.

The agent may summarize those facts, but it must not:

- turn Config non-compliance into claims of exploitability or attacker activity;
- treat Config convergence as provider readback;
- invent account/resource identifiers;
- turn user intent into authorization.

!!! note "Personal lab / POC"
    This public repository documents a personal learning/demo environment. It is not a production service and does not authorize changes to company or production infrastructure.
