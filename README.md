# AWS Compliance Agent — Frozen Reference Repository

> **This is the old/reference repository. New product development continues in [`amitkarpe/awsops`](https://github.com/amitkarpe/awsops).**

This repository preserves the proven Compliance Agent v1 implementation, historical R&D, browser/E2E evidence, and migration source material.

## Development status

**FROZEN FOR NEW PRODUCT WORK**

Do not start here:

- new controls;
- new roadmap milestones;
- new runtime/deployment architecture;
- new product features;
- new AWS mutation paths.

Use this repository only to inspect and selectively harvest proven patterns into `awsops`.

Canonical migration roadmap:

- [awsops Issue #1 — clean migration from aws-secops to awsops](https://github.com/amitkarpe/awsops/issues/1)
- [awsops Issue #11 — M3 native Reject acceptance](https://github.com/amitkarpe/awsops/issues/11)
- [awsops PR #13 — isolated normal-auth/native Reject canary](https://github.com/amitkarpe/awsops/pull/13)

## Stable historical baseline

The immutable `compliance-agent-v1.0.0` release remains useful historical evidence for:

- four-account Config status;
- S3 Block Public Access remediation;
- restricted SSH remediation;
- exact freeze + native Approve/Reject;
- provider readback;
- Config convergence;
- authenticated Reject-only E2E;
- rich native cards and browser integration.

## Open legacy R&D

- **PR #192**: deep `s3_ssl` Reject-only Playwright/native-browser research. Treat as a harvest source for `awsops`, not as the future product branch.
- **PR #177**: read-only persistent MCP evidence adapter. Treat as deferred reference material; rewrite selectively only if a future `awsops` milestone needs it.

## Migration rule

**Selective port, not repository copy.**

Classify old work as:

- **KEEP** — proven reusable contract/test/pattern;
- **REWRITE** — useful idea coupled to the old architecture;
- **LEAVE BEHIND** — obsolete rollout/runtime baggage or experiments.

The old repository remains available for evidence/history until the new repository reaches cutover and archival acceptance.
