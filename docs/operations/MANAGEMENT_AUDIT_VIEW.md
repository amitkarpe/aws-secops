# Management audit view

Authority: Issue #85  
Evidence source: completed Issue #82 live acceptance on 2026-09-18.

## Executive outcome

| Control | Reject | Approve | Provider readback | Re-run |
| --- | --- | --- | --- | --- |
| S3 Block Public Access | 0 writes | 4 exact BPA updates | **VERIFIED** | **ALREADY_COMPLIANT**, 0 writes |
| Security Group restricted SSH | 0 writes | 4 exact SSH revocations | **VERIFIED** | **ALREADY_COMPLIANT**, 0 writes |

Target aliases: `lab-dev`, `lab-poc`, `lab-qa`, `lab-sec`.

## What management should take away

1. **The agent did not get broad AWS write access.** M/Harness remained read-only.
2. **Human decisions stayed separate by control.** S3 approval did not authorize Security Group remediation.
3. **Reject caused no AWS mutation.** Each rejected frozen batch produced zero writes.
4. **Approved changes used a bounded execution path.** O = GitHub OIDC performed the exact control-specific actions.
5. **Provider readback proved completion.** AWS Config remained an independent asynchronous evidence source.

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
AWS Config result
```

Interpretation:

- `REJECTED` -> exact tool is **NOT_CALLED**.
- `APPROVED` -> only the exact frozen control batch may execute.
- Provider readback is the remediation truth.
- AWS Config may lag or be unavailable without invalidating a successful provider readback.

## Acceptance evidence

### S3 Block Public Access

- one empty tagged demo bucket per alias;
- no objects, public policy, public ACL, or website hosting;
- Reject -> **0 writes**;
- Approve -> **4 exact bucket-level BPA updates**;
- provider readback -> all four aliases **VERIFIED**;
- re-run -> **ALREADY_COMPLIANT**, 0 writes.

### Security Group restricted SSH

- one tagged unattached demo Security Group per alias;
- deliberate test condition: TCP/22 from `0.0.0.0/0`;
- Reject -> **0 writes**;
- Approve -> **4 exact unrestricted-SSH revocations**;
- provider readback -> all four aliases **VERIFIED**;
- re-run -> **ALREADY_COMPLIANT**, 0 writes.

## AWS Config evidence

During final Issue #82 acceptance, AWS Config was:

- `UNAVAILABLE` for both supported controls;
- `UNAVAILABLE` across all four aliases;
- reported separately from provider verification;
- never used to authorize a write.

This is intentional: **Config is evidence, not execution authority**.

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
