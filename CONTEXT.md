# Agent Context

This file is compact **current-only** restart state for ChatGPT/coding-agent continuity.

Repository: `amitkarpe/aws-secops`

## Current Product Truth

- Demo v1 live acceptance remains established for the personal Singapore lab.
- Supported remediation families remain **S3 Block Public Access** and **Security Group restricted SSH**.
- Approved mutation remains explicit human decision -> exact bounded execution -> direct provider readback.
- `aws_secops_operator` AgentCore Harness remains read-only; M/AWS MCP remains read-only.
- Four-account read-only Harness overview is live for `lab-dev`, `lab-poc`, `lab-qa`, and `lab-sec`.
- Platform Issue #32 proved the existing O = GitHub OIDC path can obtain controller-only tagged admin sessions across registered personal LAB accounts while MCP/Harness sessions remain read-only.

## Current Operating Model

> **M discovers/verifies; Git/IaC declares; O applies; provider readback proves.**

- **M** = ChatGPT AWS MCP.
- **O** = GitHub OIDC.
- G/ChatGPT Web is the normal controller.
- GitHub is durable engineering state.
- X/Codex is used only when a cohesive local/runtime/bootstrap step cannot be completed through G's connectors.

## Active Authority

**Issue #82 / PR #83 — multi-account S3 + SG + AWS Config E2E**

Target aliases are exactly:

- `lab-dev`
- `lab-poc`
- `lab-qa`
- `lab-sec`

The E2E milestone uses the two already-implemented controls:

1. `s3-bucket-level-public-access-prohibited`
2. `restricted-ssh`

For each alias the campaign owns one empty tagged demo S3 bucket and one tagged unattached demo Security Group.

### Safe demo preparation

- S3: empty bucket only; no public policy, public ACL, website, or user data; bucket-level BPA may be deliberately re-armed non-compliant for the demo.
- SG: unattached demo group only; one deliberate TCP/22 ingress from `0.0.0.0/0`.
- Preparation is operator/OIDC-only and never exposed as a Harness tool.

### Frozen batches and approvals

- S3 and SG remain **separate frozen four-target batches**.
- S3 and SG require **independent decisions**.
- Reject means zero writes for that exact batch.
- Approve runs only through the existing OIDC `AccessMode=oidc-lab-admin` session path.
- No generic model-accessible AWS admin tool is added.

### Evidence truth

- Direct S3/EC2 provider readback is remediation truth.
- AWS Config is asynchronous evidence for the same two controls.
- Config `NON_COMPLIANT` after verified provider remediation is reported as `PENDING`, not failure.
- Missing/unhealthy Config is reported as `UNAVAILABLE`/unverified; Config alone never authorizes mutation.
- Default/public output is alias-only; account IDs, ARNs, bucket names, SG IDs, and session credentials remain hidden.

## Supporting Platform Work

aws-platform Issue #34 / PR #35 adds a main-only OIDC campaign runner that reuses the existing controller and existing target role. It resolves exactly the four approved LAB aliases privately, checks out aws-secops main, and supports:

`prepare -> plan -> execute(reject|approve)`

No new AWS role/trust model is introduced.

## Safety Boundary

- No office/work/Synapxe scope.
- No generic model-accessible AWS mutation.
- M/Harness remain read-only.
- Only the exact demo resources are mutable.
- S3 demo resources stay empty and non-public.
- SG demo resources stay unattached.
- Destructive/unrelated actions remain outside Issue #82.
- Historical evidence is not standing proof; live OIDC execution and provider readback are required.

## Next Actions

1. Finish PR #83 implementation/tests/docs and supporting platform PR #35.
2. Merge code only after exact-head CI review.
3. Run the main-only OIDC sequence: prepare -> S3 plan/reject/approve -> SG plan/reject/approve.
4. Verify provider readback for all eight remediations and report Config convergence separately.
5. Update public status only after live acceptance passes.

For product/security rules use `SPEC.md`. For longer history use closed Issues/PRs and Git history.
