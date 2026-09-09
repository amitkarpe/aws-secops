# aws-secops

**AWS Copilot** — a proposed AWS security and compliance copilot built around Amazon Bedrock AgentCore, human governance, exact tools, provider verification, and audit.

## Current Phase

This repository is currently in **Phase 0: proposal + technical feasibility**.

The near-term goal is not to rush into a full clean implementation before management approval. The working R&D proof remains in [`mytestlab123/AgentCore`](https://github.com/mytestlab123/AgentCore); this repository defines the proposed long-term product direction and the technical questions that must be validated next.

## Start Here

1. Read `AGENTS.md` for repository rules.
2. Read `CONTEXT.md` for current truth and next action.
3. Read `SPEC.md` for the active Phase 0A contract.
4. Read `docs/ARCHITECTURE.md` for the proposed future-state architecture.
5. Read `ROADMAP.md` for proposal -> personal-lab feasibility -> pilot sequencing.

## Proposed Direction

```text
thin UI / approval experience
  -> AgentCore Harness
  -> MCP Gateway + Policy
  -> exact governed tool
  -> workload IAM / STS
  -> target AWS account
  -> provider verification + audit
```

The model is not the authorization boundary. Provider-native findings/state and deterministic controls remain authoritative.

## Proven vs Proposed

**PROVEN in the R&D repo:** real human approval, AgentCore Gateway/Policy enforcement, real Security Group remediation, and provider re-verification.

**PROPOSED for the clean product:** Harness-first specialist agents, actual governed tools behind Gateway, clean workload IAM, later multi-account STS/Organizations, model benchmarking, and scalable provider-backed controls.

**TO VALIDATE next:** current AgentCore/Bedrock Region behavior, Harness/Runtime boundaries, model access/cost, hosting cost, and scale economics using the isolated standalone personal lab.
