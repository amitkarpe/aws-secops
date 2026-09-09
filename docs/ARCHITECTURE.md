# Architecture Decision v1

Status: accepted for MVP-1

Source research:

- https://github.com/mytestlab123/AgentCore/blob/main/docs/research/aws-copilot/ARCHITECTURE_DECISION_V1.md
- https://github.com/mytestlab123/AgentCore/blob/main/docs/research/aws-copilot/KIRO_DEEP_REVIEW_RESULT_2026-09-09.md

## Product goal

AWS Copilot is a security/compliance copilot that uses AWS provider truth, human governance, deterministic AgentCore Policy, exact remediation tools, provider verification, and audit.

It is **not** another scanner and the model is **not** the security boundary.

## MVP-1 architecture

```text
thin approval UI / LibreChat initially
        |
        v
AgentCore Harness
Compliance Agent
ap-southeast-1
        |
        v
MCP AgentCore Gateway
        |
AgentCore Policy
        |
        +--> exact read Lambda MCP tool
        |
        +--> exact remediation Lambda MCP tool
        |
        v
workload IAM / STS
        |
        v
approved member dev/sandbox account
        |
        v
real Security Group
        |
        v
provider re-read + compact audit
```

## Decisions

### Harness first

Use AgentCore Harness for the specialist agent loop. Move to custom Runtime orchestration only when a concrete Harness limitation appears.

### Govern the actual action

The actual read/remediation tool invocation goes through MCP Gateway + Policy. Do not reproduce the old POC pattern of asking Gateway for a separate authorization decision and then independently mutating AWS outside that governed tool call.

### Exact tools first

For the first small controls, prefer tiny Lambda targets exposed as MCP tools. A Runtime-hosted MCP server is justified only when shared state, long-running behavior, richer protocol logic, or reusable server behavior makes it simpler.

### Member account workload

The Organizations management account is administrative/bootstrap context only. The product workload belongs in an approved member dev/sandbox or later dedicated security-tooling account.

### Multi-account later

Scale through central AgentCore execution plus fixed cross-account STS roles:

```text
central tool execution role
   -> AwsCopilotReadRole
   -> AwsCopilotRemediationRole
```

Account/OU/Region/role/action mappings are server-owned or allowlisted. The model never supplies an arbitrary role ARN or AWS action for execution.

### Provider truth

Use direct AWS APIs or provider-native findings. The expected product value chain is:

```text
provider finding/state
-> specialist explanation
-> human decision when mutating
-> Gateway Policy
-> exact remediation
-> provider verification
-> audit
```

### Agents

Sequence:

1. Compliance Agent.
2. Vulnerability Agent using Inspector/ECR provider findings.
3. Manual agent switching.
4. Supervisor/A2A only if routing later adds measurable value.

### Registry

Keep agents/tools/skills descriptor-ready for AWS Agent Registry, but Registry is not an MVP dependency. Registry Region and record IDs remain deployment configuration.

### Human approval

MVP-1 can use a thin UI/LibreChat/Harness client handoff for approval. Do not claim this event is automatically visible to Temporal Policy.

A later milestone may introduce a trusted approval event plus Temporal Policy for `detect -> approve -> remediate -> verify`.

### Models

Model choice is replaceable. Benchmark Nova 2 Lite against a stronger candidate on actual security tasks. Gateway Policy, exact tools, and IAM remain unchanged regardless of model.

## Public repository boundary

The repository is public. Source code and generic IaC/policies belong here; personal/company environment identity does not.

Do not commit:

- account IDs or environment-specific ARNs;
- credentials/tokens/session data/private keys;
- emails/private endpoints;
- raw private audit/finding evidence.

The private runtime/demo may display real non-secret provider identifiers when the operator needs them.

## MVP-1 exclusions

No Registry dependency, StackSets rollout, Security Hub/Inspector rollout, Temporal Policy, WAF, EKS, Supervisor/A2A, custom scanner, or second control.
