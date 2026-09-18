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
- `ops.astromedicomp.org` shows live four-account organization Config evidence.
- `sec.astromedicomp.org` supports live four-account status, planning, and **native Approve/Reject execution** for those exact two controls.
- The retained 100-S3 / 10-SG runtime is explicitly legacy/single-account.
- Direct S3/EC2 provider readback is remediation truth.
- AWS Config is independent asynchronous evidence.

## Accepted Four-Account Chat Execution

Issue #100 is LIVE-ACCEPTED.

Exact flow:

```text
live Config evidence
  -> read-only plan
  -> freeze exact four-account batch
  -> LibreChat native Approve / Reject
  -> fixed CodeBuild project
  -> GitHub App + AWS CodeConnections source from aws-secops@main
  -> existing G/O controller role
  -> exact four target sessions
  -> existing Issue #82 guarded AWS action
  -> direct provider readback
  -> independent Config convergence
```

### S3

Batch: `79677c056ccfe4a2aeee`

- native hook: ASK;
- Reject simulation: **0 CodeBuild execution dispatch**;
- Approve through actual MCP executor: **4 exact BPA updates**;
- execution backend: **AWS CodeBuild via GitHub CodeConnections**;
- provider readback: **VERIFIED x4**;
- Config convergence: **COMPLIANT x4**.

### Security Group

Batch: `850a97336aded01e0aa1`

- native hook: ASK;
- Reject simulation: **0 CodeBuild execution dispatch**;
- Approve through actual MCP executor: **4 exact unrestricted-SSH revocations**;
- execution backend: **AWS CodeBuild via GitHub CodeConnections**;
- provider readback: **VERIFIED x4**;
- Config convergence: **COMPLIANT x4**.

### Idempotent guard

After both controls were compliant:

- four-account plan returned no non-compliant aliases;
- `chat_execution_available=false` for both controls;
- both prepare calls failed closed as ineligible;
- CodeBuild build count did not increase.

## Final Demo State

The four demo accounts were re-armed after acceptance.

Current expected starting state for Amit's browser demo:

- S3: `NON_COMPLIANT x4`;
- restricted SSH: `NON_COMPLIANT x4`;
- Operator + Compliance Agent both use that live Config evidence.

## Runtime

- `aws-secops-bulk.service`: active.
- `aws-secops-librechat.service`: active.
- Exactly one live AWS Compliance Agent record.
- Agent has the four-account prepare + executor tools.
- Executor is native `ASK`, never static allow.
- S3 and SG approvals remain separate.
- No Config automatic remediation.
- No SCP change.
- No generic model-accessible AWS admin tool.

## Operating Model

> **Read evidence -> recommend -> freeze exact batch -> native decision -> fixed CodeBuild/G/O controller -> provider proves -> Config independently evidences.**

- Reject means no execution dispatch.
- Approve applies only the exact frozen control + batch.
- Public/default output remains alias-only.
- Raw account IDs, ARNs, bucket names, SG IDs and credentials remain hidden.
- Personal LAB only; no Synapxe/work/office scope.
- X/Codex is fallback only.

## Completed Authority

- Issue #100 / PRs #101–#104: native chat approval + CodeBuild execution for exact four-account S3/SG scope.
- Issue #95 / PRs #96–#99: live four-account web/agent default scope.
- Issue #93 / PR #94: acceptance evidence on web tools.
- Issue #88 / PRs #89–#91: organization Config bootstrap.
- Issue #87 / PR #92: management rehearsal.
- Issue #82 / PRs #83–#84: four-account provider E2E.

## Next

Improve the management-facing Operator Center GUI without changing the accepted execution boundary.

For product/security rules use `SPEC.md`.
