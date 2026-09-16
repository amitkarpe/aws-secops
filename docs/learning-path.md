# Learning path

Use this page as the **beginner reading order**. It separates the current live read/investigation architecture from the recorded Demo v1 mutation proof and from older research/history.

## 1. Understand the current system first

Read these in order:

1. [Home](index.md) — what the project is trying to achieve.
2. [3-minute demo](operations/AGENTIC_DEMO_3_MIN.md) — the shortest current operator/executive story.
3. [Current architecture](architecture.md) — live read/investigation plane versus governed mutation plane.
4. [Governance](governance.md) — why prompt intent cannot create AWS write authority.
5. [Project status](project-status.md) — what is actually live, recorded, blocked and still planned.
6. [Long Demo v1](demo-v1.md) — the recorded S3 BPA + restricted-SSH remediation walkthrough.

!!! important "Current architecture"
    The `aws_secops_operator` AgentCore Harness is **live today as the read-only operator/investigation layer**. It exposes exactly four bounded read tools. The recorded Demo v1 human-approval + Gateway/Policy + exact-tool path remains the separate mutation proof. Do not describe the Harness as the remediation executor.

## 2. Understand the evidence boundary

Three distinctions matter most:

- **AWS Config evidence** is not the same as direct provider state.
- **Config-only `CLEAR`** means no current bounded non-compliant finding was returned; provider state may still be `NOT_READ` and risk `NOT_ASSESSED`.
- **Recommendation** is not authorization; AWS mutation remains behind the separate governed path.

The [Governance](governance.md) page explains these boundaries in detail.

## 3. Then learn how the AgentCore work evolved

Continue with the [AgentCore Research & Learning hub](research/index.md) for component-level background and earlier experiments.

Recommended order:

1. [AgentCore Research & Learning](research/index.md) — component mental model and historical context.
2. [Harness operator experiments](research/agentcore-harness-operator-experiments.md) — pre-deployment investigation that informed the current live Harness.
3. [AgentCore feature matrix](research/AGENTCORE_FEATURE_MATRIX.md) — which AgentCore component solves which problem.
4. [Gateway + Policy live proof](research/GATEWAY_POLICY_LIVE_PROOF.md) — earlier feasibility evidence for governed exact tools.
5. [Harness runtime proof](research/HARNESS_NOVA2_LITE_LIVE_PROOF.md) — earlier runtime feasibility observations.

These pages are valuable engineering history. Where they conflict with `PROJECT_STATUS.md`, current Architecture/Governance, or Issue #60 acceptance evidence, the newer current sources win.

## 4. Read technical proof when you need evidence

- [Reliability hardening](implementation/RELIABILITY_HARDENING_PROOF.md) — Config termination, SG safe-stop recovery, truthful status and AWS-free validation.
- [Governed S3 execution proof](implementation/PLATFORM_PHASE11_13_PROOF.md) — recorded exact S3 execution path.
- [PR #25](https://github.com/amitkarpe/aws-secops/pull/25) — Config + exact restricted-SSH direction.
- [PR #27](https://github.com/amitkarpe/aws-secops/pull/27) — recorded Demo v1 acceptance.
- [Issue #60](https://github.com/amitkarpe/aws-secops/issues/60) — current Harness deployment, failure-mode, healthy-path and security-boundary evidence.

## 5. Operations

For current presentation/use:

- [3-minute demo](operations/AGENTIC_DEMO_3_MIN.md) — use this first.
- [Long Demo v1](demo-v1.md) — use when you need the recorded mutation story.
- [Cost and cleanup](operations/COST_AND_CLEANUP.md)

The older [LibreChat bulk demo](operations/LIBRECHAT_BULK_DEMO.md) remains S3-specific historical operations material; it is not the current live Harness walkthrough.

## 6. Historical material

These pages explain how the project evolved, but they are not current architecture authority:

- [Earlier multi-source pilot demo](operations/DEMO_SCRIPT.md)
- [Phase 0B research plan](research/PHASE0B_PLAN.md)
- older dated plans and proofs under `docs/implementation/`

## Future direction

- [Operations Console direction](operator-console.md)
- [Roadmap](roadmap.md)

Issue #60 Milestone 3 remains blocked pending a second explicitly authorized owned AWS read scope. Do not infer a live multi-account capability from code or historical plans alone.

## Reading rule

For current human-facing truth, prefer `README.md`, `PROJECT_STATUS.md`, current Architecture/Governance, Issue #60 acceptance evidence and this curated site. `CONTEXT.md` is for coding-agent/session continuity rather than the public introduction.
