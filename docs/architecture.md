# Architecture

The design separates **reasoning**, **authorization**, **execution** and **verification**. No single prompt or model response is treated as the security boundary.

## Control path

| Layer | Responsibility | What it must not do |
|---|---|---|
| AWS Config | Detect compliance state | Authorize remediation |
| AWS Compliance Agent | Read, explain, summarize and plan | Invent arbitrary AWS mutation scope |
| Human approval | Accept or reject an exact action family | Prove execution succeeded |
| AgentCore Gateway | Expose the bounded tool entry point | Replace Policy or IAM |
| AgentCore Policy | Independently ALLOW or DENY the exact invocation | Trust model confidence |
| Exact tool | Perform one narrow S3 or SG action | Become a generic AWS CLI/API surface |
| Provider readback | Verify actual AWS state | Assume Config has already converged |

```text
Signal          Plan              Decision          Governance       Mutation          Evidence
AWS Config  ->  Compliance Agent  -> Human ASK  -> Gateway/Policy -> Exact tool    -> AWS readback
```

## Detection scope is broader than remediation scope

AWS Config can report compliance for resources across the account/Region. The remediation system deliberately uses a smaller intersection:

```text
AWS Config finding
        +
server-owned retained manifest
        +
current provider safety guards
        =
eligible exact remediation batch
```

A model-generated resource ID is not sufficient to expand this scope.

## Two independent action families

Demo v1 supports S3 BPA and restricted SSH. `Fix all` may prepare both families, but their approval and execution remain independent.

```text
Fix all
  ├─ S3 exact batch -> S3 Approve / Reject -> S3 Gateway/Policy/tool
  └─ SG exact batch -> SG Approve / Reject -> SG Gateway/Policy/tool
```

A UI may allow two decisions to be submitted together; this does not turn them into one blanket approval.

## Immediate truth vs asynchronous evidence

After a mutation, direct provider readback determines the immediate remediation result.

AWS Config remains valuable independent evidence, but it can converge later. The UI and agent therefore distinguish:

- **Provider verified** — current AWS state was re-read and matches the approved target.
- **Config status** — asynchronous compliance evaluation from AWS Config.

## Reliability

The execution model preserves durable state and explicit uncertainty:

- immutable batch/approval identity binds scope;
- terminal jobs cannot be silently replayed;
- `RUNNING`, `FAILED` and `UNKNOWN` are distinct states;
- uncertain writes are not blindly retried;
- `UNKNOWN` is resolved through read-only provider reconciliation;
- success requires matching provider evidence.

For the deeper implementation history, see the selected proofs in the **Technical proofs** section of this site.
