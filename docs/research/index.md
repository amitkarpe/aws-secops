# AgentCore Research & Learning

This section explains the **AgentCore experiments and next-direction work** in `aws-secops`.

!!! important "Current Demo v1 vs AgentCore research"
    The **current Demo v1** still uses the LibreChat AWS Compliance Agent described in [Architecture](../architecture.md). The AgentCore Harness material here is the **next operator direction and research track**. It should not be read as proof that Harness is already the primary deployed Demo v1 runtime.

If you are new to this repository, read [Start here](../learning-path.md) first. Then return here when you want to understand the AgentCore direction.

![Amazon Bedrock AgentCore Harness — how it works](../assets/agentcore-harness-flow.webp){ loading=lazy width="100%" }

*Conceptual learning map. In this repository, AWS mutation remains behind human approval, Gateway/Policy enforcement, and exact bounded tools.*

## 30-second mental model

| Component | Beginner meaning | Role in this project |
| --- | --- | --- |
| **Model** | The reasoning engine | Understands the prompt and decides what information or tool it needs |
| **Harness** | The managed agent runtime | Runs the agent loop, instructions, sessions, tools and context |
| **Gateway** | The controlled tool entrance | Exposes only approved tool interfaces to the agent |
| **Policy** | The independent allow/deny gate | Enforces whether a tool invocation is permitted |
| **Exact tool** | One narrow AWS capability | Prevents the model from getting a generic AWS mutation surface |
| **AWS Config** | Compliance evidence | Supplies findings such as S3 BPA or restricted SSH status |
| **Provider readback** | Immediate AWS truth after a change | Confirms what actually changed instead of assuming success |

!!! tip "KISS rule"
    **Model = brain · Harness = runtime/body · Gateway + Policy = guardrails · exact tools = capability boundary · provider readback = truth**

## Recommended reading order

### 1. Start with the current Harness experiment

[**Harness operator experiments**](agentcore-harness-operator-experiments.md) records the five concrete tests behind the proposed read-only `aws_secops_operator` design.

What it proves today:

- the repository security contract is testable;
- the CloudFormation design validates;
- proposed IAM policies pass Access Analyzer validation;
- required AWS Config evidence sources are available;
- incomplete/paginated evidence must remain explicitly partial.

What it does **not** prove yet:

- live operator chat through the new Harness;
- runtime model tool selection;
- live Gateway/Policy behavior for this new Harness path;
- end-to-end production readiness.

### 2. Learn the AgentCore components

Read [AgentCore feature matrix](AGENTCORE_FEATURE_MATRIX.md) when you want to understand which AgentCore component solves which problem.

### 3. Read the earlier live proofs

These are useful **feasibility proofs**, not the current product baseline:

- [Gateway + Policy live proof](GATEWAY_POLICY_LIVE_PROOF.md) — earlier evidence that exact tools can be governed by Policy.
- [Harness + Nova 2 Lite live proof](HARNESS_NOVA2_LITE_LIVE_PROOF.md) — earlier Harness runtime experimentation.

### 4. Use the reference pages only when needed

- [Model access matrix](MODEL_ACCESS_MATRIX.md) — provider/model access observations.
- [Cost model](COST_MODEL_V0.md) — planning assumptions and cost notes.
- [Connector safety framing](CHATGPT_CONNECTOR_SAFETY_FRAMING.md) — engineering lessons from ChatGPT connector safety gates.

## Current AgentCore direction

The next-direction design separates **engineering**, **operator reasoning**, and **AWS authorization**:

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

For the current Harness experiment, the operator path is deliberately **read-only**:

```text
operator prompt
   -> aws_secops_operator Harness
   -> exact Gateway tools
   -> Policy ENFORCE
   -> read-only Lambda
   -> AWS Config
   -> evidence + explanation
```

A prompt such as **"fix this"** must not create a second, easier mutation path. Remediation still follows the governed Demo v1 control path:

```text
recommend
   -> human approval
   -> exact executor
   -> Gateway / Policy
   -> exact remediation tool
   -> AWS API
   -> provider readback
```

## How to interpret evidence on this site

!!! success "Current learning"
    Work that directly informs the active AgentCore operator direction. Start with the Harness operator experiments.

!!! info "Reference"
    Design matrices, cost notes and engineering observations. Useful for decisions, but not runtime proof by themselves.

!!! warning "Historical proof"
    Earlier live experiments that proved feasibility at that point in time. They are **not automatically current deployment state**.

## Latest learning

The pagination experiment found that a bounded AWS Config S3 read returned **100 rows plus a continuation token**, while the complete read returned **107 rows**.

That reinforces one important agent rule:

> **Incomplete evidence must stay labeled partial. An agent must not turn the first page of results into a confident statement about the entire environment.**

[Open the Harness operator experiments →](agentcore-harness-operator-experiments.md)
