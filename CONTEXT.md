# Agent Context

This file is compact **current-only** restart state for ChatGPT/coding-agent continuity.

Repository: `amitkarpe/aws-secops`

## Current Product Truth

- Demo v1 live acceptance remains established for the personal Singapore lab.
- Supported remediation families remain S3 Block Public Access and restricted SSH on retained owned demo resources.
- Approved mutation remains human approval -> Gateway/Policy -> exact bounded tool -> provider readback.
- The model has no generic AWS mutation tool.
- `aws_secops_operator` remains the read-only AgentCore Harness investigation/reasoning layer; explicit `fix/apply/execute` requests do not mutate through it.
- Issue #76 is **ACTIVE** as the stakeholder-ready continuation of the Issue
  #68 hub/spoke proof.
- Personal LAB/DEV multi-account discovery intentionally permits broad read-only audit/discovery access; broad mutation is not implied.

## Current Operating Model

> **AWS MCP discovers and verifies; Git/IaC declares; GitHub OIDC applies; AWS MCP independently verifies where supported.**

ChatGPT Web is the default controller. GitHub is durable engineering state. AWS is runtime state. Use X/Codex when a cohesive implementation or runtime package materially benefits from local/profile/runtime access or deeper engineering.

## Active Authority

**Issue #76 — 3-4 account SecOps organization security overview demo**

https://github.com/amitkarpe/aws-secops/issues/76

Status: **ACTIVE**.

Current role evidence:
- the management hub can assume `ChatGPTCrossAccountReadRole` in every
  explicitly registered personal LAB target;
- each assumed target identity is re-read with STS;
- the role remains bounded to broad read/audit policies; cross-account
  remediation is not authorized;
- account-label rename is separately blocked until AWS Organizations enables
  trusted access for Account Management. Existing registered labels remain the
  safe runtime resolution fallback.

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

1. Produce the public-safe 3-4 account overview and one control drill-down
   using the live role path.
2. Keep the Platform role implementation in review; do not merge it from this
   milestone handoff.
3. Enable the separate Organizations Account Management trusted-access
   prerequisite only if Amit explicitly approves it, then apply the requested
   member display-name changes.
4. If remediation is needed later, create a separate bounded remediation role
   and milestone.

Detailed completed Issue #60/#70 acceptance, Harness history, and prior deployment evidence remain in closed Issues/PRs, docs, and Git history rather than this restart file.

For public status use `PROJECT_STATUS.md`. For the product/security contract use `SPEC.md`. For future scope use `ROADMAP.md`.
