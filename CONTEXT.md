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
- `sec.astromedicomp.org` defaults generic status/plan questions to live four-account read-only tools.
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
- Four-account chat plan is read-only and reports `chat_execution_available=false`.
- Multi-account execution path remains `separate governed GitHub OIDC G/O path`.
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

> **Read evidence -> recommend -> explicit decision -> G controls -> O applies -> provider proves -> Config independently evidences.**

- Four-account chat reads/plans do not grant mutation authority.
- Reject means zero writes for that exact batch.
- Public/default output remains alias-only.
- Raw account IDs, ARNs, bucket names, SG IDs and credentials remain hidden.
- Personal LAB only; no Synapxe/work/office scope.
- X/Codex is fallback only.

## Completed Authority

- Issue #95 / PRs #96–#98: live four-account web/agent default scope.
- Issue #93 / PR #94: acceptance evidence on web tools.
- Issue #88 / PRs #89–#91: organization Config bootstrap.
- Issue #87 / PR #92: management rehearsal.
- Issue #82 / PRs #83–#84: four-account provider E2E.

## Next

Use this four-account demo as the stable baseline. Keep CodeConnections/CodeBuild as a separate CI/CD experiment; do not replace the proven G/O trust path until its behavior is independently accepted.

For product/security rules use `SPEC.md`.
