# Learning path

Use this curated path before reading historical phase documents.

## Quick start

1. Read [Home](index.md).
2. Read [Architecture](architecture.md).
3. Read [Demo v1](demo-v1.md).
4. Read [Governance](governance.md).
5. Read [Project status](project-status.md) for the current public baseline and known limits.

## Current technical proof

Then continue with:

- [Governed S3 execution proof](implementation/PLATFORM_PHASE11_13_PROOF.md)
- [PR #25](https://github.com/amitkarpe/aws-secops/pull/25) for the Config + exact-SG/unified-agent milestone
- [PR #27](https://github.com/amitkarpe/aws-secops/pull/27) for current Config-driven planning, separate approvals and Demo v1 acceptance

## Operations

For current-family support material:

- [LibreChat bulk demo](operations/LIBRECHAT_BULK_DEMO.md) — S3-specific operations material
- [Cost and cleanup](operations/COST_AND_CLEANUP.md)

The current two-family walkthrough is [Demo v1](demo-v1.md). Do not use the older Phase 1 demo script as the primary current demo.

## Research and history

These pages are useful evidence of how the project evolved, but they are **not** the current primary architecture:

- [Historical multi-source pilot demo](operations/DEMO_SCRIPT.md)
- [Historical Harness feasibility proof](research/HARNESS_NOVA2_LITE_LIVE_PROOF.md)
- [Gateway + Policy live proof](research/GATEWAY_POLICY_LIVE_PROOF.md)
- [AgentCore feature matrix](research/AGENTCORE_FEATURE_MATRIX.md)
- [Cost model](research/COST_MODEL_V0.md)
- dated plans and proofs under `docs/implementation/`

## Future direction

- [Operations Console direction](operator-console.md)
- [Roadmap](roadmap.md)

## Reading rule

For current human-facing truth, prefer `README.md`, `PROJECT_STATUS.md`, `SPEC.md` and this curated site. `CONTEXT.md` is retained for coding-agent/session continuity and should not be treated as the public introduction.
