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

The migration-era Issue/PR backlog was closed on 2026-09-27 after the useful
generic browser patterns were harvested into `awsops`. Closed items remain fully
readable as R&D/evidence.

## Retained reference areas

### PR #192 — merged for preservation

Merged into frozen main at
`2fe201e719a3b842bde8c12189c3e602cf9f6e71` after fresh CI and exact-diff
review.

The preserved implementation remains reference material for:

- bounded live `s3_ssl` read + prepare/freeze;
- native Reject-only card assertions;
- zero-dispatch / zero-write decision receipts;
- unchanged provider readback;
- UI timing/recovery and Playwright acceptance;
- auth-safe diagnostics;
- Archive cleanup;
- relevant failure/replay/restart/readback cases.

This merge preserves completed engineering state; it does **not** reactivate
aws-secops as the product-development target.

### PR #177 — closed without merge

Reference only if a future `awsops` milestone needs:

- fixed read query contract;
- account verification;
- bounded pagination;
- partial/unavailable semantics;
- closed schema/fixtures.

## Final state

Keep this repository **preserved but frozen**. Do not archive or delete it by
default: Amit may reuse it for a different future project. Any reuse must start
with a new explicit scope and must not silently revive the old SecOps roadmap.
