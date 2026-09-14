# Learning path

Use this page as the **beginner reading order**. It separates the current Demo v1 architecture from the newer AgentCore research track so they are not confused.

## 1. Understand the current system first

Read these in order:

1. [Home](index.md) — what the project is trying to achieve.
2. [Current architecture](architecture.md) — how reasoning, approval, execution and verification are separated today.
3. [Demo v1](demo-v1.md) — the current supported S3 BPA + restricted-SSH walkthrough.
4. [Governance](governance.md) — why the model does not get broad AWS mutation authority.
5. [Project status](project-status.md) — current public baseline, known limits and what is actually live.

!!! important "Current architecture"
    Demo v1 currently uses the **LibreChat AWS Compliance Agent** with bounded tools. AgentCore Harness is an active research/next-direction track, not a replacement that should be assumed live today.

## 2. Then learn the AgentCore direction

When the current system makes sense, continue with the [AgentCore Research & Learning hub](research/index.md).

Recommended AgentCore order:

1. [AgentCore Research & Learning](research/index.md) — beginner mental model and current-vs-historical framing.
2. [Harness operator experiments](research/agentcore-harness-operator-experiments.md) — five concrete pre-deployment tests for the proposed read-only operator Harness.
3. [AgentCore feature matrix](research/AGENTCORE_FEATURE_MATRIX.md) — which AgentCore component solves which problem.
4. [Gateway + Policy live proof](research/GATEWAY_POLICY_LIVE_PROOF.md) — earlier feasibility evidence for governed exact tools.
5. [Harness runtime proof](research/HARNESS_NOVA2_LITE_LIVE_PROOF.md) — earlier Harness feasibility observations.

## 3. Read technical proof when you need evidence

[Issue #32 hardening evidence](implementation/RELIABILITY_HARDENING_PROOF.md) covers Config termination, SG safe-stop recovery, truthful status timestamps and AWS-free validation.

Then continue with:

- [Governed S3 execution proof](implementation/PLATFORM_PHASE11_13_PROOF.md)
- [PR #25](https://github.com/amitkarpe/aws-secops/pull/25) for the Config + exact-SG/unified-agent milestone
- [PR #27](https://github.com/amitkarpe/aws-secops/pull/27) for current Config-driven planning, separate approvals and Demo v1 acceptance

## 4. Operations

For operator/support material:

- [LibreChat bulk demo](operations/LIBRECHAT_BULK_DEMO.md) — S3-specific operations material
- [Cost and cleanup](operations/COST_AND_CLEANUP.md)

The current two-family walkthrough is [Demo v1](demo-v1.md). Do not use the older multi-source pilot demo as the primary current demo.

## 5. Historical material

These pages explain how the project evolved, but they are not the current primary architecture:

- [Earlier multi-source pilot demo](operations/DEMO_SCRIPT.md)
- [Phase 0B research plan](research/PHASE0B_PLAN.md)
- older dated plans and proofs under `docs/implementation/`

## Future direction

- [Operations Console direction](operator-console.md)
- [Roadmap](roadmap.md)

## Reading rule

For current human-facing truth, prefer `README.md`, `PROJECT_STATUS.md`, `SPEC.md` and this curated site. `CONTEXT.md` is for coding-agent/session continuity and should not be treated as the public introduction.
