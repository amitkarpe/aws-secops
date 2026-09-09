# AgentCore feature matrix for Singapore

Status: Phase 0B.1 research, checked 2026-09-09

Target Region: Asia Pacific (Singapore), `ap-southeast-1`

This matrix records service availability, not deployment proof. No resource was
created and no paid feature was enabled during this pass.

## Regional matrix

Unless a row says otherwise, no fallback is required because Singapore is
supported; the authoritative source is the AgentCore Regions page linked in
that row's feature name or in the source list below. The two unavailable rows
name the nearest documented fallback and do not propose cross-Region use.

| Capability | Singapore | Proposed use | Phase |
| --- | --- | --- | --- |
| AgentCore Harness | Available | Run and debug the specialist agent without managing hosting | Next experiment |
| Runtime microVM | Available | Managed session-isolated hosting when Harness is insufficient | Later / only if needed |
| Runtime Instances | Available | Longer-lived managed agent hosting | Later / only if needed |
| Gateway | Available | Expose bounded tools through a governed interface | Next experiment |
| Policy | Available | Enforce deterministic ALLOW/DENY before a controlled tool runs | Next experiment |
| Temporal Policy | Available | Time- and identity-aware Cedar authorization | Later |
| Identity | Available | Workload and user identity integration | Company pilot |
| Memory | Available | Cross-session agent context | Defer until a use case requires it |
| Observability | Available | Agent traces, metrics and logs | Next experiment |
| Evaluations | Available | Repeatable quality and safety evaluation | Company pilot |
| Optimization | Available | Cost/quality tuning after measurements exist | Later |
| Built-in tools | Available | Browser and code-interpreter capabilities | Later |
| Gateway WAF integration | Available | Regional WAF protection; fail-closed mode recommended | Internet-facing pilot only |
| Gateway rate limiting | Available | Protect capacity and control consumption | Pilot; not an authorization boundary |
| A2A on Runtime | Available | Agent-to-agent protocol support | Later |
| Step Functions `InvokeHarness` | Available | Request-response orchestration of a Harness agent | Later |
| AWS Agent Registry | **Not available** | Discover and govern agents/tools centrally | Later; Sydney is the closest listed fallback |
| Web Search built-in tool | **Not available** | Managed web search | Defer; Tokyo is a nearby supported Region |

Gateway rate limiting fails open when its rate-limit evaluation encounters a
transient failure. It is therefore a capacity/cost guard, not the hard policy
control. Authorization remains the job of AgentCore Policy and the exact tool's
own IAM and input validation.

Harness provides the built-in `shell` and `file_operations` tools by default.
Omitting `allowedTools` allows all available tools; a plain-text specialist
agent must set an explicit empty allowlist. This only restricts model tool
selection. Direct commands require the separate
`bedrock-agentcore:InvokeAgentRuntimeCommand` permission, which should remain
absent unless the product explicitly needs that API.

## Recommended Friday architecture

```text
LibreChat or thin UI
        |
        v
AgentCore Harness -- specialist agent, no separate Harness fee
        |
        v
Gateway + Policy -- bounded tool interface and deterministic authorization
        |
        v
Lambda -- exact read or controlled action
        |
        v
AWS service API -- provider truth and verification
```

- Put the agent in Harness first.
- Put each exact, deterministic tool in Lambda.
- Reuse LibreChat or a thin UI for the human interaction.
- Add Runtime-hosted MCP only when Lambda cannot meet the protocol or lifecycle
  need.
- Defer EKS: this POC does not justify its cluster cost and operating surface.
- Keep the primary deployment in Singapore. Do not add cross-Region Registry or
  Web Search dependencies to the first pilot.

## Official sources

- [AgentCore supported Regions and features](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html)
- [Temporal Policy supported Regions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-temporal.html)
- [Gateway WAF integration](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-waf.html)
- [Gateway rate limits](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-rate-limits.html)
- [Runtime A2A support](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-a2a.html)
- [Step Functions integration with AgentCore Harness](https://docs.aws.amazon.com/step-functions/latest/dg/connect-bedrockagentcore.html)
- [AWS Agent Registry regional launch information](https://aws.amazon.com/about-aws/whats-new/2026/08/aws-agent-registry-generally-available/)
- [AgentCore pricing](https://aws.amazon.com/bedrock/agentcore/pricing/)
- [Harness tools and tool isolation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-tools.html)
