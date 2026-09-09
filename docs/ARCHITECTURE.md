# Architecture Proposal v1

Status: proposed baseline for Phase 0A; not yet a clean-product implementation claim

Source research:

- https://github.com/mytestlab123/AgentCore/blob/main/docs/research/aws-copilot/ARCHITECTURE_DECISION_V1.md
- https://github.com/mytestlab123/AgentCore/blob/main/docs/research/aws-copilot/KIRO_DEEP_REVIEW_RESULT_2026-09-09.md

## Product goal

AWS Copilot is a proposed security/compliance copilot that combines AWS provider truth, specialist-agent reasoning, human governance, deterministic AgentCore Policy, exact remediation tools, provider verification, and audit.

It is **not** another scanner and the model is **not** the security boundary.

## Proposed future-state architecture

```text
thin approval UI / client
        |
        v
AgentCore Harness
specialist agent
        |
        v
MCP AgentCore Gateway
        |
AgentCore Policy
        |
        +--> exact read tool
        |
        +--> exact remediation tool
        |
        v
workload IAM / STS
        |
        v
approved AWS account(s)
        |
        v
provider re-read + audit
```

For the first small controls, tiny Lambda MCP targets remain the preferred hypothesis. That choice must be validated against current Harness/Gateway/Runtime behavior rather than treated as irreversible.

## Proven today

The earlier `mytestlab123/AgentCore` R&D repository has already demonstrated:

- human ASK / Approve / Reject behavior;
- real AgentCore Gateway invocation;
- real AgentCore Policy ALLOW / DENY;
- one real Security Group unrestricted-SSH control;
- approved exact remediation;
- provider re-read to COMPLIANT;
- compact audit evidence.

The clean `aws-secops` repository does **not** yet reimplement that entire runtime.

## Proposed decisions

### Harness first

Use AgentCore Harness for the specialist-agent loop when it is the smallest correct fit. Move to custom Runtime orchestration only when a concrete Harness limitation appears.

### Govern the actual action

The intended clean design places the actual governed tool invocation behind MCP Gateway + Policy. Avoid the old R&D split where Gateway authorization and the later AWS mutation were separate calls.

### Exact tools first

Prefer semantically narrow tools such as:

- `check_unrestricted_ssh`;
- `remove_unrestricted_ssh`;
- later `check_s3_block_public_access` / `enforce_s3_block_public_access`;
- later `check_imdsv2` / `require_imdsv2`.

Do not expose a generic AWS CLI/API mutation tool to the runtime agent.

### Provider truth

Prefer direct AWS APIs or provider-native findings rather than rebuilding scanners.

```text
provider finding/state
-> specialist explanation
-> human decision when mutating
-> Gateway Policy
-> exact remediation
-> provider verification
-> audit
```

### Personal lab now, Organizations later

For **Phase 0B technical validation**, use the isolated standalone personal lab account selected locally through `vagent`. It has passed read-only Bedrock + AgentCore Gateway + Policy preflight in Singapore and is intentionally separate from company/management environments.

For a future company pilot, the target remains a member security/tooling or non-production account, not the Organizations management account.

Later multi-account scale is expected to use central AgentCore execution plus fixed cross-account STS roles:

```text
central tool execution role
   -> AwsCopilotReadRole
   -> AwsCopilotRemediationRole
```

Account/OU/Region/role/action mappings remain server-owned or allowlisted. The model never supplies an arbitrary role ARN or AWS action for execution.

### Agents

Proposed sequence:

1. Compliance Agent.
2. Vulnerability Agent using Inspector/ECR provider findings.
3. Manual specialist switching.
4. Supervisor/A2A only if automatic routing later adds measurable value.

### Registry

Keep agents/tools/skills descriptor-ready for AWS Agent Registry, but Registry is not a first-pilot dependency. Current Region availability and cross-Region implications must be validated as part of technical research.

### Human approval

The first product pilot can use a thin UI/LibreChat/Harness client handoff for approval. Do not claim that this approval is automatically visible to Temporal Policy.

A later milestone may introduce a trusted approval event plus Temporal Policy for `detect -> approve -> remediate -> verify`.

### Models

Model choice is replaceable. Benchmark Nova 2 Lite against at least one stronger available candidate on actual AWS Copilot tasks. Gateway Policy, exact tools, and IAM remain the security boundary regardless of model.

## Scale questions to answer before a company pilot

Examples:

- 1,000 S3 buckets x 5 controls = 5,000 checks per assessment;
- 20,000 S3 buckets x 5 controls = 100,000 checks per assessment;
- daily vs weekly vs monthly assessment economics;
- 20 EC2 instances/month for vulnerability evidence, report comparison, recommendation, approval, patching and verification;
- direct provider APIs vs Config/Security Hub/Inspector where they provide existing authoritative evidence;
- model-token cost vs AgentCore/Gateway/Policy/Lambda/logging cost;
- retained-resource cost and cleanup behavior;
- Singapore vs other-Region feature availability.

## Public repository boundary

The repository is public. Source code and generic IaC/policies belong here; personal/company environment identity does not.

Do not commit:

- account IDs or environment-specific ARNs;
- credentials/tokens/session data/private keys;
- emails/private endpoints;
- raw private audit/finding evidence.

Private runtime/demo output may show real non-secret provider identifiers when needed.

## Phase 0A exclusions

No full clean runtime deployment, multi-account rollout, Registry dependency, StackSets rollout, broad Security Hub/Inspector/Config enablement, Temporal Policy, WAF, EKS, Supervisor/A2A, custom scanner, or second control implementation.