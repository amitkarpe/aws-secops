# Phase 0B.2 — Nova 2 Lite through AgentCore Harness

Status: Phase 0B.2 initial call **BLOCKED**; Phase 0B.2a least-tool call **PASS**

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

## Phase 0B.2a — explicit zero-tool proof

AWS documents that omitted `allowedTools` allows every available tool and that
an explicitly supplied list replaces the existing value. The retained Harness
was updated with an empty list. Readback reached `READY` and showed:

```text
configured tools: 0
allowedTools: []
```

Exactly one additional invocation was then made with the globally installed,
stable AgentCore CLI:

```text
CLI version: 0.28.1
prompt: Reply with exactly: HARNESS_TEXT_OK
response stream: HARNESS_TEXT_OK
tool calls: 0
stop reason: end_turn
input tokens: 65
output tokens: 8
model latency: 1,888 ms
end-to-end wall time, including cold start: 45,652 ms
```

This is a PASS. Neither `shell`, `file_operations` nor another tool appeared in
the stream. The CLI's summary envelope contained an empty text field, but the
native content delta contained the exact requested marker; acceptance uses the
stream where Harness delivers its response.

The retained execution role's inline policy was also read back. It does **not**
grant `bedrock-agentcore:InvokeAgentRuntimeCommand`. This is intentionally
separate from `allowedTools`: the allowlist controls model tool selection,
whereas direct Runtime command execution is governed by its own IAM action.

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
`invoke-harness` command. AgentCore CLI v1.0.0-preview.29 was used for the
initial call. After the official stable CLI was installed globally, Phase
0B.2a used AgentCore CLI v0.28.1. Both invoked the native Harness data plane by
Harness ARN and added no project dependency.

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

The Phase 0B.2a least-tool call cost was:

```text
input  = 65 / 1,000,000 × $0.41 = $0.00002665
output =  8 / 1,000,000 × $3.39 = $0.00002712
model total                     = $0.00005377
```

The explicit empty allowlist reduced input usage from 1,243 to 65 tokens for
these tiny prompts by removing default tool definitions and the failed tool
turn. Across both experiments, measurable model inference was approximately
**$0.00074646**.

## AWS mutations and retained state

Mutations performed:

1. created one dedicated IAM execution role;
2. attached one dedicated inline execution policy;
3. created one AgentCore Harness and its AWS-managed underlying Runtime;
4. performed one Harness invocation, which created one ephemeral session file.
5. updated the retained Harness from `allowedTools=["*"]` to `allowedTools=[]`;
6. performed one additional zero-tool Harness invocation and explicitly stopped
   its Runtime session after receiving the final response.

Readback after the invocation:

| Retained resource | State | Why retained | Idle billing |
| --- | --- | --- | --- |
| Harness | `READY`, `allowedTools=[]` | Reuse for Phase 0B.3 | No separate Harness charge |
| Managed underlying Runtime | present | Owned by the retained Harness | Active session consumption only |
| Execution role + inline policy | present | Required by the retained Harness | No IAM charge |
| Runtime log group | present, 24 streams | Native audit evidence for the next check | CloudWatch storage at actual bytes |
| Memory | disabled / absent | Not needed | none |
| Active invocation session | terminated | Invocation hit its terminal stop | none |

The retained resources are isolated, tagged for Phase 0B.2 and useful for the
immediate correction. Cleanup, if chosen after review, is a bounded
`DeleteHarness` followed by deletion of this task's inline IAM policy and role;
resource IDs and ARNs remain in private evidence rather than this public file.

## Phase 0B.3 follow-up result

The recommended Gateway experiment is now **PASS**. The retained Harness called
one exact Gateway tool; Policy permitted `dev` and Lambda ran once, while Policy
denied synthetic `prod` and Lambda ran zero additional times. Built-in tools and
direct `InvokeAgentRuntimeCommand` remain unavailable. See
`GATEWAY_POLICY_LIVE_PROOF.md`.

## Official sources

- [Harness models and invocation overrides](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-models.html)
- [Harness tools and `allowedTools`](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-tools.html)
- [Harness security and execution role](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-security.html)
- [Harness observability and cost controls](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-operations.html)
- [AgentCore CLI reference](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-cli-reference.html)
- [CreateHarness API](https://docs.aws.amazon.com/bedrock-agentcore-control/latest/APIReference/API_CreateHarness.html)
- [AgentCore pricing](https://aws.amazon.com/bedrock/agentcore/pricing/)
- [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/)
