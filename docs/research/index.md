# AgentCore Research & Learning

This is the **learning hub** for the AWS SecOps AgentCore work: what we tested, what we proved, what is still experimental, and what remains historical reference.

![Amazon Bedrock AgentCore Harness — how it works](../assets/agentcore-harness-flow.webp){ loading=lazy width="100%" }

*Conceptual learning map for AgentCore Harness. In this repository, AWS mutation stays behind the existing human-approval → Gateway/Policy → exact-tool boundary.*

!!! tip "KISS mental model"
    **Model = brain · Harness = agent runtime/body · Gateway + Policy = guardrails · exact tools = capability boundary · AWS readback = truth**

## Start here

| Page | Why read it | Status |
| --- | --- | --- |
| [Harness operator experiments](agentcore-harness-operator-experiments.md) | Five concrete tests behind the new read-only SecOps operator design | **Current learning** |
| [AgentCore feature matrix](AGENTCORE_FEATURE_MATRIX.md) | Understand which AgentCore components solve which problem | Reference |
| [Gateway + Policy live proof](GATEWAY_POLICY_LIVE_PROOF.md) | Earlier proof that policy enforcement can govern exact AgentCore tools | Historical proof |
| [Harness + Nova 2 Lite live proof](HARNESS_NOVA2_LITE_LIVE_PROOF.md) | Earlier Harness feasibility work and runtime observations | Historical proof |
| [Model access matrix](MODEL_ACCESS_MATRIX.md) | Model/provider access observations used during experiments | Reference |
| [Cost model](COST_MODEL_V0.md) | Cost assumptions and planning notes | Planning |
| [Connector safety framing](CHATGPT_CONNECTOR_SAFETY_FRAMING.md) | Engineering lessons around ChatGPT connector safety gates | Engineering reference |

## Current product direction

The current design separates **engineering**, **operator reasoning**, and **AWS authorization** instead of giving the model broad AWS permissions.

```text
ChatGPT + GitHub + OIDC
        |
        | engineering / deployment
        v
Operator -> AgentCore Harness
               |
               v
        AgentCore Gateway
               |
          Policy ENFORCE
               |
          exact AWS tool
               |
              AWS
               |
        readback / evidence
```

For the current Harness milestone, the operator side is intentionally **read-only**:

```text
operator prompt
   -> aws_secops_operator Harness
   -> exact Gateway tools
   -> Policy ENFORCE
   -> read-only Lambda
   -> AWS Config
   -> evidence + explanation
```

A prompt such as **"fix this"** must not create an alternate mutation path. Remediation still follows the existing governed flow:

```text
recommend
   -> human approval
   -> exact executor
   -> Gateway / Policy
   -> exact remediation tool
   -> AWS API
   -> provider readback
```

## How to read the evidence

!!! success "Current learning"
    Work that directly informs the active `aws_secops_operator` direction. Start with the Harness operator experiments.

!!! info "Reference"
    Useful design matrices, cost notes, and engineering observations. These inform decisions but are not themselves runtime proof.

!!! warning "Historical proof"
    Valuable experiments from earlier milestones. They prove feasibility at that point in time, but they are **not automatically current production state**.

## Latest learning

The most useful recent finding came from the pagination experiment: a bounded AWS Config S3 read returned **100 rows plus a continuation token**, while the complete read returned **107 rows**.

That small experiment reinforces a major agent-design rule:

> **Incomplete evidence must be labeled partial; the agent must not turn a first page into a confident claim about the whole environment.**

[Open the full Harness operator experiments →](agentcore-harness-operator-experiments.md)
