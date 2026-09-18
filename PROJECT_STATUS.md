# Project Status

**Current public baseline:** the four-account personal-LAB SecOps demo is live-proven for both supported remediation families. Read-only investigation remains separate from governed GitHub OIDC execution.

## Current live scope

Target aliases:

- `lab-dev`
- `lab-poc`
- `lab-qa`
- `lab-sec`

Supported controls:

1. S3 bucket-level Block Public Access
2. Security Group restricted SSH

Operating model:

`read-only evidence -> recommendation -> explicit control-specific decision -> OIDC tagged-admin execution -> direct provider readback -> Config evidence`

## Issue #82 — completed multi-account remediation proof

Live acceptance completed on 2026-09-18.

### S3

- safe preparation: PASS;
- frozen four-target batch: PASS;
- Reject: **0 writes**;
- Approve: **4 exact BPA updates**;
- direct S3 provider readback: **VERIFIED**;
- rerun plan: **ALREADY_COMPLIANT**, 0 writes.

### Security Group

- safe preparation: PASS;
- frozen four-target batch: PASS;
- Reject: **0 writes**;
- Approve: **4 exact unrestricted-SSH revocations**;
- direct EC2 provider readback: **VERIFIED**;
- rerun plan: **ALREADY_COMPLIANT**, 0 writes.

### AWS Config

During final acceptance, Config evidence was `UNAVAILABLE` for both controls on all four aliases.

This is reported explicitly and does not override provider truth. Config remains evidence-only and never authorizes a write.

## Trust boundary

- **G = ChatGPT** controls the durable GitHub workflow.
- **O = GitHub OIDC** is the bounded mutation path.
- **M = AWS MCP** remains read-only.
- `aws_secops_operator` AgentCore Harness remains read-only.
- S3 and SG approvals remain separate.
- Reject performs zero writes.
- No generic model-accessible AWS administration tool is exposed.
- Default/public output hides account IDs, ARNs, bucket names, SG IDs, and credentials.
- Personal LAB only; no Synapxe/work/office authority.

## Earlier accepted milestones

- Issue #60: contextual investigation + Decision Timeline.
- Issue #70: bounded CloudTrail recent-change attribution.
- Issue #76 / PR #79: public-safe multi-account read-only overview.
- Issue #80 / PR #81: live AgentCore Harness multi-account overview.

Historical implementation and acceptance evidence remain in closed Issues/PRs and Git history.

## Known limits

- This is a bounded LAB demo, not arbitrary-resource or production remediation.
- AWS Config was unavailable during Issue #82 final acceptance.
- A Config finding does not prove exploitability, sensitive-data exposure, attacker activity, or business impact.
- CloudTrail Event History records API activity; it does not prove human identity or intent.
- The Harness and M do not receive mutation authority.

## Current work

Issue #82 is complete. The next bounded milestone is **management-facing evidence/audit visualization**.

Contributors and coding agents use `CONTEXT.md` for current restart state and `SPEC.md` for the product/security contract.
