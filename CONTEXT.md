# Agent Context

Repository: `amitkarpe/aws-secops`  
Status: ACTIVE  
Updated: 2026-09-18

> Current-only restart state. History belongs in closed Issues/PRs and Git history.

## Current Product Truth

- **Issue #82 is live-accepted** across exactly `lab-dev`, `lab-poc`, `lab-qa`, and `lab-sec`.
- Supported remediation families:
  1. `s3-bucket-level-public-access-prohibited`
  2. `restricted-ssh`
- G/ChatGPT controls the workflow; **O = GitHub OIDC** performs bounded writes.
- M/AWS MCP and `aws_secops_operator` AgentCore Harness remain read-only.
- Direct S3/EC2 provider readback is remediation truth.
- AWS Config remains an independent asynchronous evidence plane. Issue #88 is bootstrapping Config recording + the two exact organization rules so the four-account demo can show real compliance convergence.

## Live Issue #82 Acceptance

Target aliases:

- `lab-dev`
- `lab-poc`
- `lab-qa`
- `lab-sec`

### Preparation

PASS across all four aliases:

- one empty tagged demo S3 bucket per alias;
- no public policy, public ACL, website, objects, or user data;
- one tagged unattached demo Security Group per alias;
- one deliberate TCP/22 ingress from `0.0.0.0/0`.

### S3 batch

Frozen batch: `79677c056ccfe4a2aeee`

- plan: four pending aliases, zero mutations;
- Reject: **0 mutations**;
- Approve: **4 exact BPA updates**;
- provider readback: **VERIFIED**;
- rerun plan: `ALREADY_COMPLIANT`, 0 mutations, provider verified.

### Security Group batch

Frozen batch: `850a97336aded01e0aa1`

- plan: four pending aliases, zero mutations;
- Reject: **0 mutations**;
- Approve: **4 exact unrestricted-SSH revocations**;
- provider readback: **VERIFIED**;
- rerun plan: `ALREADY_COMPLIANT`, 0 mutations, provider verified.

### Config evidence

For both controls and all four aliases:

- `UNAVAILABLE`
- reported explicitly;
- never treated as provider failure;
- never used to authorize mutation.

## Operating Model

> **M/Harness discover and reason; Git declares; G controls; O applies; provider readback proves.**

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
- Destructive/unrelated AWS actions are outside Issue #82.

## Current Authority

- aws-secops Issue #88: organization-wide AWS Config evidence for the four-account demo.
- aws-platform Issue #44: bounded G/O bootstrap command for Issue #88.
- aws-secops Issue #82 / PR #83/#84: completed provider E2E baseline.

## Next

Merge the Issue #88 bootstrap implementation, run the bounded Config bootstrap, then repeat the S3 + SG Reject/Approve flow and verify Config convergence.

For product/security rules use `SPEC.md`. For history use closed Issues/PRs and Git history.
