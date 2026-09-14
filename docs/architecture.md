# Architecture

The design separates **reasoning**, **authorization**, **execution** and **verification**. No single prompt or model response is treated as the security boundary.

## Current Demo v1 architecture

The current primary agent is a LibreChat AWS Compliance Agent using native Bedrock Nova 2 Lite with bounded MCP tools. Earlier AgentCore Harness work remains useful research/history, but Harness is **not** the current primary Demo v1 execution architecture.

```text
AWS Config
   ↓ compliance evidence
LibreChat — AWS Compliance Agent
   ↓ read / explain / plan
Server-owned planner + retained manifests
   ↓ exact family + immutable batch
Native human Approve / Reject
   ↓ approved exact intent
AgentCore Gateway (IAM-authenticated)
   ↓
AgentCore Policy (ENFORCE)
   ↓ ALLOW / DENY
Exact family tool / Lambda
   ↓
AWS API
   ↓
Direct provider readback
   ↓
Durable batch result

AWS Config converges independently after provider state changes.
```

## Control path

| Layer | Responsibility | What it must not do |
|---|---|---|
| AWS Config | Detect compliance state | Authorize remediation |
| AWS Compliance Agent | Read, explain, summarize and plan | Invent arbitrary AWS mutation scope |
| Server-owned planner | Intersect supported control + retained manifest + current readiness | Accept model-selected arbitrary targets |
| Human approval | Accept or reject an exact action family | Prove execution succeeded |
| AgentCore Gateway | Expose the bounded tool entry point | Replace Policy or IAM |
| AgentCore Policy | Independently ALLOW or DENY the exact invocation | Trust model confidence |
| Exact tool | Perform one narrow S3 or SG action | Become a generic AWS CLI/API surface |
| Provider readback | Verify actual AWS state | Assume Config has already converged |

## Detection scope is broader than remediation scope

AWS Config can report compliance for resources across the account/Region. The remediation system deliberately uses a smaller intersection:

```text
AWS Config finding
        +
server-owned retained manifest
        +
current provider safety guards
        =
eligible exact remediation family
```

A model-generated resource ID is not sufficient to expand this scope.

### Current readiness rule

Demo v1 planners are conservative: a supported family is prepared only when the **complete retained family** satisfies the current readiness/eligibility conditions. The implementation does not claim arbitrary-subset remediation such as fixing 3 of 100 retained buckets from a model-selected list.

## Two independent action families

Demo v1 supports S3 BPA and restricted SSH. `Fix all` may prepare both families, but their approval and execution remain independent.

```text
Fix all
  ├─ S3 exact batch -> S3 Approve / Reject -> S3 Gateway/Policy/tool
  └─ SG exact batch -> SG Approve / Reject -> SG Gateway/Policy/tool
```

A UI may allow two decisions to be submitted together; this does not turn them into one blanket approval.

## Separate operator-maintenance path

The Operator UI has a different purpose from normal chat remediation:

```text
Authenticated operator
   ↓
Prepare-demo preview
   ↓ one-use confirmation
Exact guarded demo reset
   ↓
Provider checks
   ↓
Fresh pending batch
```

This path deliberately restores the owned lab resources to the known non-compliant demo state. It is not an agent tool, it is not remediation approval, and it does not replace the normal human approval + Gateway/Policy path used to fix the resources.

## Immediate truth vs asynchronous evidence

After a mutation, direct provider readback determines the immediate remediation result.

AWS Config remains valuable independent evidence, but it can converge later. The UI and agent therefore distinguish:

- **Provider verified** — current AWS state was re-read and matches the approved target.
- **Config status** — asynchronous compliance evaluation from AWS Config.

The Operator cards identify their evidence sources: **saved S3 batch readback** versus **current EC2 status read**. New S3 verification events persist their own timestamps; old journals retain their counts but show **not recorded** when no verification timestamp exists. File modification time is not a verification event. Refresh is not a fresh S3 scan, and the newest item's verification time does not prove all resources are still compliant.

## Reliability

The execution model preserves durable state and explicit uncertainty:

- immutable batch/approval identity binds scope;
- terminal jobs cannot be silently replayed;
- `RUNNING`, `FAILED` and `UNKNOWN` are distinct states;
- uncertain writes are not blindly retried;
- `UNKNOWN` is resolved through read-only provider reconciliation;
- success requires matching provider evidence.

### Safe stop, not automatic replay

The Issue #32 hardening expires **unstarted** SG approvals on restart or after an uncertain batch stop. Those items become workflow `FAILED` with **not dispatched**, while uncertain in-flight effects remain `UNKNOWN`. Already in-flight calls are allowed to finish before remaining work is expired. Read-only reconciliation is blocked while execution is active.

After uncertainty is resolved, the existing owner-operated full-manifest preview path can retain the old journal and create a new pending batch. The consumed approval cannot restart the old SG batch; later execution needs fresh approval and the same Gateway/Policy path. Normal chat planning still enforces complete-family readiness, so mixed recovery is not automatic subset remediation.

These are offline-tested recovery cases, not live production-recovery certification. Read the [hardening proof and remaining limits](implementation/RELIABILITY_HARDENING_PROOF.md).

### Bounded Config reads

Each supported rule read checks recorder health and stops after at most **10 evaluation pages or 250 results**. Valid empty pages can continue within that budget. A cap yields `partial=true`; invalid or repeated tokens fail closed. The UI distinguishes partial evidence from a complete healthy assessment. These are local safety budgets, not AWS rate limits.

For current evidence, read [Demo v1](demo-v1.md). Historical Harness and earlier pilot material are retained under **History / Research** and should not be confused with this current architecture.
