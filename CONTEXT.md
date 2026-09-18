# Agent Context

Repository: `amitkarpe/aws-secops`  
Status: ACTIVE  
Updated: 2026-09-18

> Current-only restart state. History belongs in closed Issues/PRs and Git history.

## Current Product Truth

- Primary demo scope is exactly `lab-dev`, `lab-poc`, `lab-qa`, `lab-sec`.
- Supported controls:
  1. `s3-bucket-level-public-access-prohibited`
  2. `restricted-ssh`
- `ops.astromedicomp.org` defaults to live four-account organization Config evidence.
- `sec.astromedicomp.org` defaults generic status/plan questions to live four-account tools; Issue #100 is adding native-approved execution for the same exact scope.
- The retained 100-S3 / 10-SG runtime is explicitly legacy/single-account.
- G/ChatGPT controls the durable workflow; **O = GitHub OIDC** performs bounded four-account writes.
- Direct S3/EC2 provider readback is remediation truth.
- AWS Config is independent asynchronous evidence.

## Latest Four-Account Acceptance

### S3

Batch: `79677c056ccfe4a2aeee`

- prepared: `SAFE_NONCOMPLIANT`;
- Config before: `NON_COMPLIANT x4`;
- Reject: **0 writes**;
- Approve: **4 exact BPA updates**;
- provider readback: **VERIFIED x4**;
- Config after convergence: **COMPLIANT x4**;
- rerun: `ALREADY_COMPLIANT`, 0 writes.

### Security Group

Batch: `850a97336aded01e0aa1`

- prepared: `SAFE_NONCOMPLIANT_UNATTACHED`;
- Config before: `NON_COMPLIANT x4`;
- Reject: **0 writes**;
- Approve: **4 exact unrestricted-SSH revocations**;
- provider readback: **VERIFIED x4**;
- Config after convergence: **COMPLIANT x4**;
- rerun: `ALREADY_COMPLIANT`, 0 writes.

## Web / Agent Acceptance

- Operator backend scope: `four-account-live-config`.
- Operator returns exactly four aliases and both controls.
- Compliance Agent `get_multi_account_status`: PASS.
- Compliance Agent `get_multi_account_remediation_plan`: PASS.
- Four-account status/plan remain read-only. When all four aliases for one control are `NON_COMPLIANT`, Issue #100 may freeze one exact batch and present native LibreChat Approve/Reject.
- Approved chat execution uses one fixed CodeBuild project sourced from `amitkarpe/aws-secops@main`, then assumes the existing G/O controller role; existing target-role trust remains unchanged.
- Live LibreChat agent contains the four-account default-scope instructions and both four-account tools.
- `sec.astromedicomp.org` local TLS route: HTTP 200.
- `ops.astromedicomp.org` local TLS route: HTTP 401 without Basic Auth, as expected.

## Organization Config

- recorders + delivery active across all four aliases;
- both organization managed rules deployed;
- organization aggregator in `ap-southeast-1`;
- no Config automatic remediation;
- no SCP change required.

## Operating Model

> **Read evidence -> recommend -> freeze exact batch -> native decision -> fixed CodeBuild/G/O controller -> provider proves -> Config independently evidences.**

- Four-account reads/plans do not grant mutation authority; only the exact Issue #100 native-ASK executor may dispatch a frozen control + batch.
- Reject means zero writes for that exact batch.
- Public/default output remains alias-only.
- Raw account IDs, ARNs, bucket names, SG IDs and credentials remain hidden.
- Personal LAB only; no Synapxe/work/office scope.
- X/Codex is fallback only.

## Current Authority

- Issue #100: native chat approval + CodeBuild execution for the exact four-account S3/SG scope.

## Completed Authority

- Issue #95 / PRs #96–#99: live four-account web/agent default scope.
- Issue #93 / PR #94: acceptance evidence on web tools.
- Issue #88 / PRs #89–#91: organization Config bootstrap.
- Issue #87 / PR #92: management rehearsal.
- Issue #82 / PRs #83–#84: four-account provider E2E.

## Next

Complete Issue #100 implementation, deploy the fixed CodeBuild executor and native approval hook, then run 2–3 rounds of Reject/Approve/provider/Config acceptance before Amit's browser test.

For product/security rules use `SPEC.md`.
