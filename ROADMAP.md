# Roadmap — Frozen Reference

This repository no longer owns active product development.

Canonical roadmap: **[`amitkarpe/awsops#1`](https://github.com/amitkarpe/awsops/issues/1)**.

## Historical completed baseline

- Compliance Agent v1 four-account / two-control baseline.
- Native Approve/Reject with exact frozen scope.
- S3 BPA + restricted SSH bounded remediation.
- Provider readback + AWS Config convergence.
- Authenticated Reject-only browser/API E2E.
- Rich native card/browser integration.
- Exception/audit and `s3_ssl` R&D.

## Freeze rule

From 2026-09-25:

- no new product features here;
- no new controls here;
- no new roadmap milestones here;
- no new deployment/runtime architecture here;
- no parity work merely because old code exists.

Open historical PRs may remain temporarily for migration review/evidence.

## Harvest before final archival

### PR #192

Harvest only proven browser/product behavior needed by `awsops`:

- native Reject card assertions;
- UI timing/recovery;
- auth-safe diagnostics;
- Archive cleanup;
- durable receipt/readback assertions;
- relevant failure cases.

### PR #177

Harvest only if a future `awsops` milestone actually needs a persistent read-only evidence adapter:

- fixed read query contract;
- account verification;
- bounded pagination;
- partial/unavailable semantics;
- closed schema/fixtures.

## Final state

Final archive/closure decision belongs to `awsops` M5 after useful capability parity, cutover evidence and deferred-work decisions are complete.
