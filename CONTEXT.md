# Agent Context

Repository: `amitkarpe/aws-secops`  
Status: ACTIVE  
Updated: 2026-09-18

> Current-only restart state. History belongs in closed Issues/PRs and Git history.

## Current Product Truth

- **Four-account S3 + Security Group E2E is live-accepted** across exactly `lab-dev`, `lab-poc`, `lab-qa`, and `lab-sec`.
- Supported remediation families:
  1. `s3-bucket-level-public-access-prohibited`
  2. `restricted-ssh`
- G/ChatGPT controls the workflow; **O = GitHub OIDC** performs bounded writes.
- M/AWS MCP and `aws_secops_operator` AgentCore Harness remain read-only.
- Direct S3/EC2 provider readback is remediation truth.
- AWS Config is now a working independent organization evidence plane and converges separately from provider verification.

## Live Acceptance

### S3

Frozen batch: `79677c056ccfe4a2aeee`

- deliberate start: Config `NON_COMPLIANT` across all four aliases;
- Reject: **0 mutations**, Config stayed `NON_COMPLIANT`;
- Approve: **4 exact BPA updates**;
- provider readback: **VERIFIED**;
- Config convergence: **COMPLIANT x4**;
- rerun: `ALREADY_COMPLIANT`, 0 mutations, provider verified, Config `COMPLIANT x4`.

### Security Group

Frozen batch: `850a97336aded01e0aa1`

- deliberate start: Config `NON_COMPLIANT` across all four aliases;
- Reject: **0 mutations**, Config stayed `NON_COMPLIANT`;
- Approve: **4 exact unrestricted-SSH revocations**;
- provider readback: **VERIFIED**;
- Config convergence: **COMPLIANT x4**;
- rerun: `ALREADY_COMPLIANT`, 0 mutations, provider verified, Config `COMPLIANT x4`.

### Organization Config

- recorder + delivery active for all four LAB aliases;
- organization rule: `s3-bucket-level-public-access-prohibited`;
- organization rule: `restricted-ssh`;
- organization aggregator in `ap-southeast-1`;
- aggregator source status: `SUCCEEDED`;
- no SCP change;
- no Config automatic remediation.

## Operating Model

> **M/Harness discover and reason; Git declares; G controls; O applies; provider readback proves; Config independently evidences.**

- GitHub is durable engineering/audit state.
- S3 and SG approvals remain independent.
- Reject means zero writes for that exact batch.
- No generic model-accessible AWS admin tool exists in aws-secops.
- Tagged OIDC admin authority is limited to the separate execution path.
- X/Codex is emergency/local-machine fallback only.

## Safety Boundary

- Personal LAB only; no Synapxe/work/office scope.
- Demo S3 buckets remain empty and non-public.
- Demo SGs remain unattached.
- Default/public output remains alias-only.
- Raw account IDs, ARNs, bucket names, SG IDs, and credentials remain hidden.

## Current Authority

- Issue #87: management-facing 3-minute demo rehearsal.
- Issue #88 / PR #89/#90/#91: organization Config bootstrap and live Config acceptance.
- Issue #82 / PR #83/#84: provider E2E baseline.

## Next

Run one no-mutation management rehearsal from the published demo + audit pages and verify the story fits in about 3 minutes.

For product/security rules use `SPEC.md`. For history use closed Issues/PRs and Git history.
