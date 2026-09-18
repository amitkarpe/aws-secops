# Architecture

The design separates **evidence**, **reasoning**, **authorization**, **execution** and **verification**.

No prompt or model response is an AWS-change security boundary.

## Current architecture

```text
AWS Organizations
      |
      v
AWS Config recorders x4
      |
      v
2 organization Config rules
      |
      v
Organization Config aggregator
      |
      +-------------------------+
      |                         |
      v                         v
ops.astromedicomp.org     sec.astromedicomp.org
live four-account UI      AWS Compliance Agent
                          status + plan only
      |                         |
      +------------+------------+
                   |
                   v
            Evidence / plan
                   |
                   v
        explicit governed decision
                   |
                   v
        G = durable GitHub control
                   |
                   v
        O = GitHub OIDC execution
                   |
                   v
      exact S3 / EC2 AWS action
                   |
                   v
       direct provider readback
                   |
                   v
       AWS Config convergence
```

Primary aliases:

- `lab-dev`
- `lab-poc`
- `lab-qa`
- `lab-sec`

Supported controls:

- `s3-bucket-level-public-access-prohibited`
- `restricted-ssh`

## Plane A — live four-account evidence

The Operator page and Compliance Agent read organization Config evidence.

The public-safe output includes aliases and compliance states only.

The live Compliance Agent provides:

- `get_multi_account_status`
- `get_multi_account_remediation_plan`

The four-account plan explicitly reports that chat execution is unavailable.

The model does not receive raw account IDs, arbitrary resource selectors, shell access or generic AWS mutation access.

## Plane B — governed four-account mutation

Four-account writes remain separate from the chat runtime.

```text
prepare exact LAB test state
        ↓
frozen exact control batch
        ↓
Reject or Approve
        ↓
GitHub OIDC tagged target session
        ↓
exact supported AWS API
        ↓
provider readback
        ↓
Config converges independently
```

Properties proven live:

- S3 Reject = 0 writes.
- S3 Approve = 4 exact BPA updates.
- SG Reject = 0 writes.
- SG Approve = 4 exact unrestricted-SSH revocations.
- provider readback verifies the change.
- rerun is `ALREADY_COMPLIANT` / 0 writes.
- Config ultimately reports `COMPLIANT x4`.

## Plane C — legacy retained single-account demo

The retained 100-S3 / 10-SG runtime remains for earlier engineering/demo evidence.

It still contains native LibreChat approval, Gateway/Policy and exact-tool flows.

It is **not the default current-status scope** and is clearly labeled legacy in the Operator page.

This preserves earlier evidence without confusing it with the current four-account architecture.

## Evidence hierarchy

| Question | Authoritative evidence |
|---|---|
| What does the organization compliance layer report? | AWS Config aggregator |
| Did the exact resource change? | Direct S3 / EC2 provider readback |
| What decision was requested? | Durable GitHub workflow |
| Did an AWS API call occur? | CloudTrail |
| What did runtime code emit? | CloudWatch / service logs |
| What is the retained legacy batch state? | Durable retained journal |

Provider verification proves remediation completion.

Config is independent asynchronous evidence and can temporarily lag a verified change.

## Authorization boundary

| Layer | Responsibility | Must not do |
|---|---|---|
| AWS Config | Detect/evidence | Authorize writes |
| Operator / Compliance Agent | Read, explain, plan | Gain write authority from prompt intent |
| GitHub control plane | Record exact decision | Become arbitrary AWS console |
| GitHub OIDC | Obtain bounded short-lived AWS session | Widen target/control scope |
| Exact AWS action | Apply one supported change | Become generic AWS API access |
| Provider readback | Verify actual state | Assume Config has already converged |

## Operator maintenance

Re-arming the safe demo resources is an explicit maintenance/testing action.

It is not a Compliance Agent mutation capability and it is not remediation approval.

## Safety boundary

- Personal LAB only.
- Exactly four approved aliases.
- Exactly two supported controls.
- No SCP change required for the current proof.
- No Config automatic remediation.
- No generic model-accessible AWS admin tool.
- Public/default output hides raw AWS identifiers.
- `UNKNOWN`, `PENDING`, `FAILED` and partial evidence are not success.

## Current evidence

- [3-minute demo](operations/AGENTIC_DEMO_3_MIN.md)
- [Management audit view](operations/MANAGEMENT_AUDIT_VIEW.md)
- [Governance](governance.md)
- [Operations Console](operator-console.md)
- [Project status](project-status.md)
