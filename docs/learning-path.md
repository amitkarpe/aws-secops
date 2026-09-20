# Learning path

Use this page as the beginner reading order. Current product truth comes first; historical experiments come later.

## 1. Understand the current system

Read:

1. [Home](index.md)
2. [Architecture](architecture.md)
3. [Governance](governance.md)
4. [Project status](project-status.md)
5. [3-minute demo](operations/AGENTIC_DEMO_3_MIN.md)

!!! important "Current architecture"
    Compliance Agent v1 is the clean current specialist: one read-only MCP tool, a strict four-account Config adapter, and a dedicated tool-free AgentCore Harness. The separate governed remediation path retains human approval and exact execution controls.

## 2. Understand the evidence boundary

Three distinctions matter most:

- Config evidence is not direct provider state.
- Recommendation is not authorization.
- Agent memory or RAG is not an audit ledger.

## 3. Study the earlier AgentCore work

Then use the [AgentCore Research & Learning hub](research/index.md).

Useful historical proofs:

- [Harness operator experiments](research/agentcore-harness-operator-experiments.md)
- [AgentCore feature matrix](research/AGENTCORE_FEATURE_MATRIX.md)
- [Gateway + Policy proof](research/GATEWAY_POLICY_LIVE_PROOF.md)
- [Harness runtime proof](research/HARNESS_NOVA2_LITE_LIVE_PROOF.md)

These explain how the current design evolved. They are not the current product authority.

## 4. Read technical proof when needed

- [Reliability hardening](implementation/RELIABILITY_HARDENING_PROOF.md)
- [Governed S3 execution proof](implementation/PLATFORM_PHASE11_13_PROOF.md)
- [Long Demo v1](demo-v1.md)
- [Management audit view](operations/MANAGEMENT_AUDIT_VIEW.md)

## 5. Current next work

- publish and verify `compliance-agent-v1.0.0`;
- close the v1 implementation/release milestone;
- evaluate Issue #130 as a read-only AWS MCP evidence source without widening mutation authority.

## Reading rule

For current truth, prefer root `README.md`, `PROJECT_STATUS.md`, `SPEC.md`, `CONTEXT.md`, and the current Architecture/Governance pages. Use older Issue #60 and phase documents as historical evidence only.
