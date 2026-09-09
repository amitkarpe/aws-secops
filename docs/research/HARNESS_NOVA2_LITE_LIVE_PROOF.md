# Phase 0B.2 — Nova 2 Lite through AgentCore Harness

Status: **BLOCKED** for the requested final text response; live Harness model
call **PASS**

Date: 2026-09-09

Region: Asia Pacific (Singapore), `ap-southeast-1`

AWS profile: local `amit` profile, selected by Amit after the `vagent` quota
request was found to be pending. Account identity was verified before mutation
and is intentionally absent from this public repository.

## Scope executed

One dedicated Harness was created with:

- Nova 2 Lite through `global.amazon.nova-2-lite-v1:0`;
- Bedrock `converse_stream` format;
- Memory disabled;
- no configured tools or skills;
- public managed network mode;
- one reasoning iteration, 96 maximum tokens and 120-second timeout;
- 60-second idle session timeout and 300-second maximum session lifetime;
- one dedicated execution role limited to Nova 2 Lite, managed-container pull,
  Harness workload identity and native telemetry writes.

No Gateway, Policy, Lambda, Memory, Registry, Browser, Code Interpreter, WAF,
MCP server or application UI was created or invoked.

## Exactly one invocation

Prompt:

```text
Reply with marker HARNESS_NOVA2_LIVE_OK and one sentence explaining what an AWS Security Group is.
```

Observed stream:

| Evidence | Result |
| --- | --- |
| Invocation attempts | **1** |
| Native CLI result | success |
| Model usage | 1,243 input, 54 output, 1,297 total tokens |
| Model-reported latency | 980 ms |
| End-to-end CLI wall time | 6,062 ms |
| First model stop reason | `tool_use` |
| Managed tool selected | `file_operations` |
| Tool result | ephemeral session file created successfully |
| Final stop reason | `max_iterations_exceeded` |
| Requested final answer | **not returned** |

The marker appeared only in the managed tool input, not as an assistant answer.
The session-local file is not an AWS infrastructure or repository change.

## Why the final response was blocked

The create request omitted `allowedTools`. The resulting Harness readback showed:

```text
configured tools: 0
allowedTools: ["*"]
```

AWS documents that all tools are allowed by default. The managed Harness still
offered `file_operations`; Nova selected it. With `maxIterations=1`, Harness
accepted the tool result but could not run the next reasoning turn needed to
produce the requested sentence.

No retry was made because the experiment contract permitted exactly one
invocation. A successful transport response is not presented as successful
task completion.

## Proof that this used Harness

- The resource was created and reached `READY` through `CreateHarness` and
  `GetHarness`.
- The invocation used the official AgentCore CLI with the returned Harness ARN,
  not `bedrock-runtime InvokeModel` or `Converse`.
- The managed Harness stream emitted message, tool-use, tool-result, metadata
  and Harness iteration-stop events.
- A new AgentCore Runtime log group appeared for the managed underlying Runtime,
  containing 13 streams. Startup records show credentials obtained from the
  dedicated execution role.
- CloudTrail recorded the matching `CreateHarness` management event. Harness
  data-plane events are represented as underlying Runtime events; this account
  did not expose a separate data event through Event History.

AWS CLI v2.36.41 exposes the Harness control-plane commands but not an
`invoke-harness` command. AgentCore CLI v1.0.0-preview.29 was therefore used for
the native Harness data-plane call by ARN. It was downloaded outside the
repository and did not add a project dependency.

## Cost and billing dimensions

Using the Phase 0B.1 Nova 2 Lite prices:

```text
input  = 1,243 / 1,000,000 × $0.41 = $0.00050963
output =    54 / 1,000,000 × $3.39 = $0.00018306
model total                         = $0.00069269
```

The measurable model cost is therefore approximately **$0.000693**, below one
tenth of one cent. Harness itself has no additional charge. Runtime bills
actual CPU and peak memory per second, and CloudWatch bills telemetry ingestion
and storage; those quantities were not present in the invocation response, so
no unsupported total is invented. No Gateway, Policy or Lambda charge occurred.

## AWS mutations and retained state

Mutations performed:

1. created one dedicated IAM execution role;
2. attached one dedicated inline execution policy;
3. created one AgentCore Harness and its AWS-managed underlying Runtime;
4. performed one Harness invocation, which created one ephemeral session file.

Readback after the invocation:

| Retained resource | State | Why retained | Idle billing |
| --- | --- | --- | --- |
| Harness | `READY` | Reuse for the one corrected follow-up | No separate Harness charge |
| Managed underlying Runtime | present | Owned by the retained Harness | Active session consumption only |
| Execution role + inline policy | present | Required by the retained Harness | No IAM charge |
| Runtime log group | present | Native audit evidence for the next check | CloudWatch storage at actual bytes |
| Memory | disabled / absent | Not needed | none |
| Active invocation session | terminated | Invocation hit its terminal stop | none |

The retained resources are isolated, tagged for Phase 0B.2 and useful for the
immediate correction. Cleanup, if chosen after review, is a bounded
`DeleteHarness` followed by deletion of this task's inline IAM policy and role;
resource IDs and ARNs remain in private evidence rather than this public file.

## Single recommended next experiment

Update only the retained Harness so readback shows an empty explicit tool
allowlist instead of `["*"]`, then perform one new tiny invocation with the same
prompt and verify a non-empty final assistant response. If the API cannot
represent an empty allowlist, use the narrowest non-callable allowlist supported
by AWS and document that product constraint. Do not add Gateway or Policy until
the basic Harness response passes.

## Official sources

- [Harness models and invocation overrides](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-models.html)
- [Harness security and execution role](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-security.html)
- [Harness observability and cost controls](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-operations.html)
- [AgentCore CLI reference](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-cli-reference.html)
- [CreateHarness API](https://docs.aws.amazon.com/bedrock-agentcore-control/latest/APIReference/API_CreateHarness.html)
- [AgentCore pricing](https://aws.amazon.com/bedrock/agentcore/pricing/)
- [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/)
