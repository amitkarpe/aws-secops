# Agent Context

Repository: `amitkarpe/aws-secops`  
Status: **FROZEN / REFERENCE**  
Updated: 2026-09-27

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

## Legacy migration backlog — CLOSED / REFERENCE

As of 2026-09-27 there are **no open Issues or PRs** in this repository.

The migration-era backlog was triaged after the useful browser/runtime learning was
harvested into `amitkarpe/awsops`:

- PR #192 — merged into main at `2fe201e719a3b842bde8c12189c3e602cf9f6e71`
  after a fresh preservation review. It retains the tested `s3_ssl`
  Reject-only / Playwright / receipt / Archive implementation while the
  repository remains frozen for new development.
- PR #177 — closed without merge; retained as deferred persistent read-only MCP
  adapter reference.
- Issues #130, #140, #164, #170, #176, #190 and #195 — closed as
  superseded/deferred reference.
- Issues #180, #182, #184 and #191 — closed as completed historical milestones.

Closed Issues/PRs remain readable and may be mined later. **Do not delete or
archive this repository.** Amit may reuse the repository for a different future
project; any such reuse must begin with a new explicit scope rather than
silently reviving the old SecOps roadmap.

## Repository rule

```text
aws-secops = frozen source/reference
awsops     = active product/development
```

G/X may inspect this repository. New implementation belongs in `awsops`.

Do not archive or delete this repository yet. Final archival belongs to `awsops` M5 after useful parity/cutover is complete.
