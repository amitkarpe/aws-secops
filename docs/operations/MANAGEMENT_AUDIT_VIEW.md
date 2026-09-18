# Management audit view

Authority: Issues #82, #88, #87  
Evidence source: completed four-account live acceptance on 2026-09-18.

## Executive outcome

| Control | Reject | Approve | Provider readback | AWS Config | Re-run |
| --- | --- | --- | --- | --- | --- |
| S3 Block Public Access | 0 writes | 4 exact BPA updates | **VERIFIED** | **COMPLIANT x4** | **ALREADY_COMPLIANT**, 0 writes |
| Security Group restricted SSH | 0 writes | 4 exact SSH revocations | **VERIFIED** | **COMPLIANT x4** | **ALREADY_COMPLIANT**, 0 writes |

Target aliases: `lab-dev`, `lab-poc`, `lab-qa`, `lab-sec`.

## What management should take away

1. **The agent did not get broad AWS write access.** M/Harness remained read-only.
2. **Human decisions stayed separate by control.** S3 approval did not authorize Security Group remediation.
3. **Reject caused no AWS mutation.** Each rejected frozen batch produced zero writes.
4. **Approved changes used a bounded execution path.** O = GitHub OIDC performed the exact control-specific actions.
5. **Provider readback proved completion; AWS Config independently converged to COMPLIANT.**

## Governed audit path

```text
Finding
  ↓
Bounded investigation
  ↓
Recommendation
  ↓
Human decision
  ↓
Exact GitHub OIDC action
  ↓
Provider readback
  ↓
AWS Config convergence
```

Interpretation:

- `REJECTED` -> exact tool is **NOT_CALLED**.
- `APPROVED` -> only the exact frozen control batch may execute.
- Provider readback is the remediation truth.
- AWS Config is independent asynchronous evidence and may briefly show `PENDING` after provider verification.

## Acceptance evidence

### S3 Block Public Access

- one empty tagged demo bucket per alias;
- no objects, public policy, public ACL, or website hosting;
- initial Config result -> **NON_COMPLIANT x4**;
- Reject -> **0 writes**, Config stayed **NON_COMPLIANT x4**;
- Approve -> **4 exact bucket-level BPA updates**;
- provider readback -> all four aliases **VERIFIED**;
- Config convergence -> **COMPLIANT x4**;
- re-run -> **ALREADY_COMPLIANT**, 0 writes, provider verified, Config **COMPLIANT x4**.

### Security Group restricted SSH

- one tagged unattached demo Security Group per alias;
- deliberate test condition: TCP/22 from `0.0.0.0/0`;
- initial Config result -> **NON_COMPLIANT x4**;
- Reject -> **0 writes**, Config stayed **NON_COMPLIANT x4**;
- Approve -> **4 exact unrestricted-SSH revocations**;
- provider readback -> all four aliases **VERIFIED**;
- Config convergence -> **COMPLIANT x4**;
- re-run -> **ALREADY_COMPLIANT**, 0 writes, provider verified, Config **COMPLIANT x4**.

## AWS Config evidence plane

Issue #88 added the missing organization evidence layer:

- Config recorder running in all four LAB accounts;
- central Config delivery working;
- organization managed rule: `s3-bucket-level-public-access-prohibited`;
- organization managed rule: `restricted-ssh`;
- organization Config aggregator in `ap-southeast-1`;
- aggregator source status: **SUCCEEDED**;
- no SCP change;
- no Config automatic remediation.

The final acceptance proved the full evidence transition:

`NON_COMPLIANT -> provider VERIFIED -> PENDING -> COMPLIANT`

Config remains **evidence, not execution authority**.

## Public-safe boundary

This page intentionally exposes aliases and outcome state only.

Hidden by default:

- AWS account IDs;
- ARNs;
- bucket names;
- Security Group IDs;
- credentials/session material;
- private findings.

## Trust model

```text
Read-only M / Harness
        ↓
Evidence + recommendation
        ↓
Explicit control-specific decision
        ↓
O = GitHub OIDC
        ↓
Exact bounded AWS action
        ↓
Direct provider readback
        ↓
Independent AWS Config evidence
```

The key control is simple: **AI may investigate and recommend; it does not authorize the AWS change.**
