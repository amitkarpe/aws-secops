# Agent Context

Repository: `amitkarpe/aws-secops`  
Status: **FROZEN / REFERENCE**  
Updated: 2026-09-25

> This repository is the **old implementation/reference repository**. New product engineering moved to `amitkarpe/awsops`.

## Canonical development target

- New product repository: `amitkarpe/awsops`
- Owning migration roadmap: `amitkarpe/awsops#1`
- Current clean M3 acceptance: `amitkarpe/awsops#11` / PR `#13`

Do not start new features, controls, roadmap work, runtime architecture, or deployment work here.

## What remains authoritative here

Keep this repository as historical/reference evidence for:

- immutable `compliance-agent-v1.0.0` release;
- accepted four-account / two-control Compliance Agent v1 behavior;
- S3 BPA + restricted SSH bounded execution patterns;
- native Approve/Reject and provider-readback evidence;
- exception/audit experiments;
- browser/Playwright learning and recovery evidence;
- historical deployment/runbook context.

## Open legacy PRs

### PR #192 — s3_ssl Reject-only R&D

Status: **REFERENCE / HARVEST SOURCE — DO NOT CONTINUE PRODUCT DEVELOPMENT HERE**

Useful material may be selectively harvested into `awsops` PR #13:

- native card exactness;
- Reject-only Playwright behavior;
- rendered-state timing/recovery;
- auth-safe request observation;
- durable decision/readback assertions;
- native Archive cleanup;
- race/replay/restart/source-drift/readback failure cases.

Do not copy the old retained-host deployment/runtime architecture wholesale.

### PR #177 — persistent read-only MCP adapter

Status: **REFERENCE / DEFERRED HARVEST — DO NOT CONTINUE PRODUCT DEVELOPMENT HERE**

Useful ideas may be selectively rewritten in `awsops` if a future milestone needs them:

- fixed query surface;
- per-page account verification;
- bounded pagination/result caps;
- explicit partial/unavailable evidence;
- secret-shaped field rejection;
- closed schema + fixtures.

Do not port it merely for parity.

## Repository rule

```text
aws-secops = frozen source/reference
awsops     = active product/development
```

G/X may inspect this repository. New implementation belongs in `awsops`.

Do not archive or delete this repository yet. Final archival belongs to `awsops` M5 after useful parity/cutover is complete.
