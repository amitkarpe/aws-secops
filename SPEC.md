# Specification

Status: **Demo v1 live acceptance is recorded. Issue #32 hardens the same scope; new code requires separate deployment validation.**

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
- Each rule read requires a healthy recorder and is bounded to 250 results and 10 evaluation-page requests. These are application safeguards, not AWS service quotas. Exhausted limits return `partial=true`; repeated/cyclic/malformed continuation tokens fail the read. Incomplete evidence must not prepare remediation.

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

### Bounded SG interruption recovery

Issue #32 implements safe terminalization, not automatic replay:

- On process recovery, a claimed `RUNNING` item becomes `UNKNOWN`. Unclaimed `APPROVED` items become `FAILED` with `changed=false` and an explicit **not dispatched** reason.
- An uncertain worker outcome stops further claims. Already in-flight calls finish; then unclaimed work is terminalized. Failure to launch the worker also expires unstarted work.
- Reconciliation is read-only and is rejected while that family's worker or a `RUNNING` item is active. An unavailable read leaves `UNKNOWN` unresolved. A matching read proves state, not which caller caused a change.
- The old SG approval remains consumed. It cannot start the old batch again. A fresh full-manifest preview can be created only after uncertainty is resolved and existing preview limits/guards pass; it preserves the prior journal and requires a new approval before execution.
- The normal Config-driven planner still requires complete-family readiness. Mixed compliant/non-compliant recovery is **not** a new automatic chat/subset-retry capability. Do not edit journals or reset resources merely to clear a failure.

These cases are tested with offline providers. They do not certify every filesystem/process failure, live interruption recovery, or production availability. See [hardening evidence](docs/implementation/RELIABILITY_HARDENING_PROOF.md).

## Trust assumptions

Demo v1 trusts the retained host/deployment configuration, LibreChat approval configuration, reverse-proxy/operator protection, server-owned manifests and durable local state, and the installed Gateway/Policy/tool configuration.

The demo does not claim hostile multi-tenant isolation, tamper-proof approval records, production identity governance or complete host-wide IAM isolation.

## Operator / admin boundary

The current Operator UI supports bounded demo preparation, status and troubleshooting. Raw batch IDs and `/bulk` are engineering details.

`Prepare demo` is a separate confirmed operator-maintenance path. It deliberately changes only the owned lab resources back to the known non-compliant demo state after provider guards. It is not exposed as an agent reset tool and is not remediation approval.

S3 Operator status is saved batch evidence, not a fresh S3 scan. New successful S3 readbacks persist per-item `verified_at`; the card reports the latest saved readback event. Old journals lacking those timestamps show **not recorded**, never a guessed time from file modification or batch creation. The latest event is not an all-resource freshness guarantee. SG status performs current EC2 reads and reports unknowns explicitly. Partial Config counts remain labeled partial and cannot erase the saved provider/batch metrics.

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
