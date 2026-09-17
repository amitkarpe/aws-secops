# Agent Context

This file is compact **current-only** restart state for ChatGPT/coding-agent continuity.

Repository: `amitkarpe/aws-secops`

## Current Product Truth

- Demo v1 live acceptance remains established for the personal Singapore lab.
- Supported remediation families remain S3 Block Public Access and restricted SSH on retained owned demo resources.
- Approved mutation remains human approval -> Gateway/Policy -> exact bounded tool -> provider readback.
- The model has no generic AWS mutation tool.
- `aws_secops_operator` remains the read-only AgentCore Harness investigation/reasoning layer; explicit `fix/apply/execute` requests do not mutate through it.
- Issue #68 is **ACTIVE** after the `management-lab` prerequisite passed on 2026-09-17.
- Personal LAB/DEV multi-account discovery intentionally permits broad read-only audit/discovery access; broad mutation is not implied.

## Current Operating Model

> **AWS MCP discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS MCP independently verifies where supported.**

ChatGPT Web is the default controller. GitHub is durable engineering state. AWS is runtime state. Use X/Codex when a cohesive implementation or runtime package materially benefits from local/profile/runtime access or deeper engineering.

## Active Authority

**Issue #68 — multi-account read-only SecOps proof: 2-account gate -> 3-4 account demo**

https://github.com/amitkarpe/aws-secops/issues/68

Status: **ACTIVE**.

Prerequisite evidence already passed:
- private AWS Platform `management-lab` Environment exists;
- local AWS CLI profile hint `amit` passed expected account-identity and `ap-southeast-1` Region equality checks;
- that bootstrap made no AWS resource, IAM, OIDC, remediation, or workload change.

Current contract:
- use one ChatGPT/AWS-MCP-visible hub account plus a reusable broad read-only spoke role;
- first prove the 2-account path end-to-end;
- allow broad read/list/get/describe-style discovery needed for inventory, IAM/policy, compliance, and audit visibility;
- keep representative mutation APIs denied through the read role;
- after the 2-account gate passes, scale the same contract to 3-4 explicitly registered owned LAB/DEV accounts;
- keep cross-account remediation as a separate later role and milestone.

Preferred topology:

```text
ChatGPT / AWS MCP
       |
       v
active SecOps hub account
       |
       +-- AssumeRole -> registered LAB/DEV account A (broad read-only)
       +-- AssumeRole -> management-lab (broad read-only)
       +-- AssumeRole -> later registered account C/D (broad read-only)
```

## Safety Boundary

- No generic model-accessible AWS mutation tool.
- Cross-account remediation is out of scope for the Issue #68 read role.
- Destructive or irreversible actions still require explicit approval.
- Connector Safety Gate remains mandatory.
- Do not hard-code unnecessary private account identifiers into this public repository; discover and verify live identity where practical.
- Historical acceptance evidence is not standing runtime proof; re-verify current AWS state when a task depends on it.

## Next Actions

1. Define the reusable hub/spoke broad read-only role contract in Git/IaC, using the actual AWS-MCP-visible hub identity verified at runtime rather than hard-coding private account IDs here.
2. Prove the first 2-account path end-to-end: hub identity -> AssumeRole -> account-distinguished inventory/security evidence -> zero mutation.
3. After that gate passes, register/reuse the same role contract for 1-2 more owned LAB/DEV accounts and present a 3-4 account security overview for the stakeholder demo.
4. If remediation is needed later, create a separate bounded remediation role and milestone.

Detailed completed Issue #60/#70 acceptance, Harness history, and prior deployment evidence remain in closed Issues/PRs, docs, and Git history rather than this restart file.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future scope use `ROADMAP.md`.
