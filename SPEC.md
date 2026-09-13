# Specification

Status: **Demo v1 implemented, validated and frozen.**

This file defines the current trusted contract. Historical phase-specific authority and proofs remain under `docs/implementation/` and `docs/research/`.

## Problem

AWS Config and other security tools can detect compliance findings, but operations teams still need a safe path from **finding -> explanation -> approval -> exact remediation -> verified evidence**.

The project must accelerate that path **without giving the model broad AWS mutation authority**.

## Current supported scope

Demo v1 supports exactly two remediation families in the personal Singapore lab.

### S3 Block Public Access

- retained, server-owned empty demo buckets only;
- target state: all four bucket-level Block Public Access settings enabled;
- exact resource scope comes from the server-owned retained manifest, never model-supplied bucket IDs;
- provider readback is required before reporting completion.

### Security Group restricted SSH

- retained, server-owned **unattached** demo Security Groups only;
- exact action: remove unrestricted TCP/22 ingress from `0.0.0.0/0`;
- the model cannot choose arbitrary Security Group IDs, ports, CIDRs or APIs;
- provider readback is required before reporting completion.

## Detection and eligibility

- AWS Config is the current compliance detection source.
- Config may observe resources outside the remediation demo scope.
- A finding is eligible only when it also matches the exact server-owned retained scope and current provider guards.
- Current planners are conservative: a family is prepared only when the **complete retained family** satisfies the required readiness/eligibility conditions. Demo v1 does not claim arbitrary-subset remediation.
- Imported or external findings are not automatically authorization to mutate AWS.
- Config convergence is asynchronous; successful provider readback may precede Config reporting COMPLIANT.

## Agent behavior

### Read-only intent

For read, check, explain, summarize, recommend, plan or explicit no-change requests:

- use read/planning tools only;
- do not call an executor;
- do not create an AWS mutation merely because a recommendation exists.

Recorded tests/smokes support this behavior, but the read-only/execution distinction is not the sole AWS authorization boundary.

### Explicit execution intent

Only an explicit current request to fix/apply/execute may prepare remediation.

- the server decides currently eligible families and exact resource scope;
- for `fix all`, S3 and SG remain separate action families;
- the model must not invent or edit resource IDs, account, Region, role, API, action, target or approval identity.

## Human approval

- Every supported action family requires a native LibreChat human decision.
- S3 approval and SG approval are independent.
- A UI control that submits multiple decisions together is only batching of separate decisions; it is not blanket authorization.
- Reject/cancel means that exact executor request does not dispatch.
- There is no session-wide `Approve All` capability.
- The batch/approval identity binds exact workflow scope. Demo v1 does not claim that a named human identity is itself evaluated by the later Policy decision.

## Execution governance

Approved execution follows the bounded control path:

```text
Human approval
   ↓
Exact batch executor
   ↓
AgentCore Gateway
   ↓
Policy ALLOW / DENY
   ↓
Exact remediation tool
   ↓
AWS API
   ↓
Provider readback
```

### MUST

- keep the model separate from the authorization boundary;
- expose only exact bounded remediation tools;
- independently enforce Gateway/Policy before the AWS change;
- persist durable execution state before/around network mutation as required by the current worker contract;
- verify AWS provider state after execution;
- report partial, failed and unknown outcomes honestly;
- preserve the existing owned demo-resource guards;
- keep private runtime evidence outside the public repository.

### MUST NOT

- no generic AWS CLI/API mutation tool for the model;
- no caller/model-selected arbitrary AWS resource IDs at execution time;
- no cross-account write path in Demo v1;
- no company, production or Organizations-management resources;
- no WAF/third-control claim in Demo v1;
- no automatic retry of an uncertain mutation;
- no claim that model text, approval, Gateway invocation or Config timing alone proves success;
- no claim of complete host-wide least-privilege certification from this demo;
- no credentials, account IDs, private ARNs/endpoints, auth material, session IDs, raw private findings or private screenshots in Git.

## Reliability contract

- immutable batch identity/approval data must bind the approved scope;
- terminal batches cannot be silently replayed;
- uncertain execution becomes an explicit non-success state and is resolved through read-only provider reconciliation;
- successful completion requires matching direct provider evidence;
- AWS Config is independent evidence and may lag provider truth;
- CloudTrail and CloudWatch remain authoritative AWS audit/log sources where applicable.

### Current reliability limitation

Demo v1 has restart detection and read-only reconciliation for uncertain Security Group work, but complete continuation/terminalization of every remaining approved SG item after every possible mid-batch interruption is not yet a production guarantee. Any runtime correction for this belongs in a separate explicitly authorized hardening milestone with targeted tests.

## Trust assumptions

Demo v1 trusts the retained host/deployment configuration, LibreChat approval configuration, reverse-proxy/operator protection, server-owned manifests and durable local state, and the installed Gateway/Policy/tool configuration.

The demo does not claim hostile multi-tenant isolation, tamper-proof approval records, production identity governance or complete host-wide IAM isolation.

## Operator / admin boundary

The current Operator UI supports bounded demo preparation, status and troubleshooting. Raw batch IDs and `/bulk` are engineering details.

`Prepare demo` is a separate confirmed operator-maintenance path. It deliberately changes only the owned lab resources back to the known non-compliant demo state after provider guards. It is not exposed as an agent reset tool and is not remediation approval.

Current status evidence should be described precisely: S3 Operator status is primarily saved durable batch/provider-verification evidence rather than a fresh full S3 provider scan on every UI refresh; SG status includes current provider reads.

Long term, an Operations Console may aggregate:

- platform/service health;
- remediation history and progress;
- approvals and Policy outcomes;
- correlation links into CloudTrail, CloudWatch and Config;
- provider verification and uncertain-state reconciliation.

It must not become a generic arbitrary-AWS mutation console.

## Publication / documentation contract

The repository and GitHub Pages site are public learning material.

- documentation may explain architecture, sanitized evidence, runbooks and historical experiments;
- current user-facing pages must distinguish proven Demo v1 behavior from research or future work;
- historical Harness, multi-source pilot and phase documents remain evidence/history, not current primary architecture;
- `README.md`, `PROJECT_STATUS.md`, this `SPEC.md`, and `ROADMAP.md` describe the current public project contract;
- `CONTEXT.md` is retained for coding-agent/session continuity and is not the human public introduction.

## Change authority

Any future expansion of mutation scope, resource families, accounts, identity model or production use requires a new explicit milestone with its own safety/verification acceptance. Reviewer feedback should drive that next milestone rather than silently expanding Demo v1.
