# Specification

Status: **Four-account live Config evidence is accepted. Issue #100 is the active milestone for native-chat approval of the two exact four-account remediation families.**

This file defines the current trusted contract. Historical phase-specific authority and proofs remain under `docs/implementation/` and `docs/research/`.

## Problem

AWS Config and other security tools can detect compliance findings, but operations teams still need a safe path from **finding -> explanation -> approval -> exact remediation -> verified evidence**.

The project must accelerate that path **without giving the model broad AWS mutation authority**.

## Personal LAB / DEV operating principle

This project is a personal learning/demo lab. For these explicitly registered personal LAB/DEV accounts, optimize for **demonstration velocity, broad visibility, and repeatable automation** rather than spending engineering time repeatedly micro-tuning read permissions service-by-service.

### Broad read-only is intentional

For registered personal LAB/DEV accounts:

- a reusable broad read-only role is acceptable and preferred over many narrow per-service read policies;
- the role may cover account/resource/security inventory such as read/list/get/describe operations across AWS services, including IAM/account metadata needed to explain effective permissions and security posture;
- exact implementation may use an AWS-managed broad read-only policy or an equivalent repo-owned read-only policy, provided representative mutation actions remain denied;
- do not repeatedly narrow the read role merely to satisfy least-privilege aesthetics when doing so slows the lab/demo without reducing mutation authority;
- account inclusion must still be explicit and registered; do not auto-enroll company, work, production, or unrelated accounts.

Broad **read** authority does not imply broad **write** authority.

### ChatGPT/AWS-MCP hub-and-spoke model

AWS Core/MCP may expose only one AWS account/session directly. The preferred multi-account pattern is therefore:

```text
ChatGPT / AWS Core
       |
       | active hub AWS identity
       v
SecOps hub account
       |
       +-- sts:AssumeRole --> registered LAB/DEV account A read role
       +-- sts:AssumeRole --> registered LAB/DEV account B read role
       +-- sts:AssumeRole --> later registered account C/D read role
```

Contract:

- determine the actual hub account/principal at runtime with STS; do not hard-code private account IDs in this public repository;
- each spoke role trusts only the intended hub principal/account path;
- the hub may assume the registered spoke read roles without requiring a separate user copy/paste workflow;
- the spoke role is broad read-only for inventory, IAM/policy inspection, Config/compliance reads, CloudTrail Event History and other non-mutating evidence needed by the demo;
- representative write APIs must remain denied through the read role;
- no cross-account remediation authority is inherited by the read role;
- cross-account mutation, if later required for a demo, uses a separate role/path and separate milestone.

### Multi-account acceptance sequence

Issue #68 uses staged acceptance rather than keeping the product permanently limited to two accounts:

1. **2-account gate** — prove hub identity, one spoke role, account-distinguished evidence, and zero mutation.
2. **3-4 account demo** — reuse the same contract for additional explicitly registered owned LAB/DEV accounts.
3. **Later only** — evaluate one governed cross-account remediation path through a separate role and separate reviewed milestone.

The first two-account proof is the debugging/acceptance gate, not the final product ceiling.

### Issue #100 governed four-account chat execution

Issue #100 is the explicit reviewed mutation milestone anticipated by the staged sequence above.

It permits one additional bounded execution path for exactly the four registered personal-LAB aliases and exactly the two existing controls:

```text
explicit fix intent
   ↓
server-owned frozen four-account plan
   ↓
native LibreChat Approve / Reject
   ↓
fixed CodeBuild project
   ↓
GitHub App / AWS CodeConnections source: amitkarpe/aws-secops@main
   ↓
existing G/O controller role
   ↓
exact target sessions + existing Issue #82 provider guards
   ↓
exact S3 or EC2 action
   ↓
direct provider readback
   ↓
independent AWS Config convergence
```

Contract:

- planning remains read-only and may freeze only one exact control at a time;
- execution accepts only the server-returned control + frozen batch id;
- S3 and SG remain separate approvals;
- Reject means no CodeBuild execution dispatch;
- the chat/model never selects account IDs, resource IDs, role, Region, repository, branch, buildspec, AWS API, action, CIDR, port or arbitrary environment overrides;
- CodeBuild may assume only the existing G/O controller role;
- the existing target-role trust and Issue #82 safety/provider guards remain unchanged;
- direct provider readback is required before success is reported;
- Config remains independent asynchronous evidence;
- this does not authorize company/work/production scope, new controls, SCP mutation, Config auto-remediation or generic AWS administration.

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

For the primary four-account scope:

- use the Issue #100 frozen-plan path for one exact supported control;
- all four aliases for that control must currently be `NON_COMPLIANT`;
- the server returns one exact batch id;
- native LibreChat approval gates the exact `control + batch_id`;
- S3 and SG are separate action families and separate approvals;
- the model must not invent or edit resource IDs, account, Region, role, repository, branch, buildspec, API, action, target or approval identity.

The retained 100-S3 / 10-SG executor remains legacy/single-account and is used only when the user explicitly asks for that legacy demo.

## Human approval

- Every supported action family requires a native LibreChat human decision.
- S3 approval and SG approval are independent.
- A UI control that submits multiple decisions together is only batching of separate decisions; it is not blanket authorization.
- Reject/cancel means that exact executor request does not dispatch.
- There is no session-wide `Approve All` capability.
- The batch/approval identity binds exact workflow scope. Demo v1 does not claim that a named human identity is itself evaluated by the later Policy decision.

## Execution governance

Approved primary four-account execution follows the Issue #100 bounded path:

```text
Human approval
   ↓
Exact frozen control + batch id
   ↓
Fixed CodeBuild project from aws-secops@main via CodeConnections
   ↓
Existing G/O controller role
   ↓
Exact target sessions
   ↓
Existing Issue #82 guarded remediation logic
   ↓
AWS API
   ↓
Provider readback
```

The retained legacy single-account demo continues to use its earlier AgentCore Gateway/Policy exact-tool path.

### MUST

- keep the model separate from the authorization boundary;
- expose only exact bounded remediation tools;
- preserve the applicable independent machine boundary before the AWS change: fixed CodeBuild/controller/Issue #82 guards for the four-account path, and Gateway/Policy for the retained legacy path;
- persist durable execution state before/around network mutation as required by the current worker contract;
- verify AWS provider state after execution;
- report partial, failed and unknown outcomes honestly;
- preserve the existing owned demo-resource guards;
- keep private runtime evidence outside the public repository.

### MUST NOT

- no generic AWS CLI/API mutation tool for the model;
- no caller/model-selected arbitrary AWS resource IDs at execution time;
- no generic or caller-selected cross-account write path; the only four-account mutation extension is the exact Issue #100 CodeBuild/controller path for the two supported controls;
- no company, production or Organizations-management workload mutation;
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

### Bounded S3 and SG interruption recovery

Issue #32 implements the same safe terminalization rule for both supported
families, not automatic replay:

- On process recovery, a claimed `RUNNING` item becomes `UNKNOWN`. Unclaimed `APPROVED` items become `FAILED` with `changed=false` and an explicit **not dispatched** reason.
- An uncertain worker outcome stops further claims. Already in-flight calls finish; then unclaimed work is terminalized. Failure to launch the worker also expires unstarted work.
- Reconciliation is read-only and is rejected while that family's worker or a `RUNNING` item is active. An unavailable read leaves `UNKNOWN` unresolved. A matching read proves state, not which caller caused a change.
- The old S3 or SG approval remains consumed. It cannot start the old batch again. A fresh full-manifest preview can be created only after uncertainty is resolved and existing preview limits/guards pass; it preserves the prior journal and requires a new approval before execution.
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

## Personal LAB demo standing authority

For the active personal-LAB SecCop / Config Console demo, Amit explicitly authorized routine bounded work to continue without repeated approval prompts.

Within an active owning Issue/PR, G may directly execute and validate:
- read-only AWS discovery, Config aggregation and affected-resource detail;
- minimal read-only IAM required by that approved evidence path;
- GUI/code/test changes and deployment;
- named demo DNS/TLS/reverse-proxy/auth configuration;
- service reload/restart needed for deployment;
- existing bounded demo re-arm paths already defined by this SPEC.

Do not stop or ask to stop the retained demo host merely because validation completed. Keep it running unless Amit explicitly requests a cost-saving shutdown.

This standing authority does not permit termination, destructive deletion, secrets publication, company/PROD mutation, generic model-accessible AWS mutation, new arbitrary controls/accounts, or unrelated IAM expansion.

## Change authority

For personal LAB/DEV **read-only** account expansion, Issue #68 and this contract permit a reusable broad read role and staged 2 -> 3-4 account proof without repeated per-service least-privilege redesign.

Issue #100 is the explicit mutation milestone for native-chat execution of the **existing two controls across the existing four registered LAB aliases only**, using the fixed CodeBuild + existing G/O controller design above.

Any future expansion beyond that exact mutation scope — new controls, arbitrary resources, additional accounts, identity-model changes, company/work accounts or production use — requires another explicit milestone with its own safety/verification acceptance.
