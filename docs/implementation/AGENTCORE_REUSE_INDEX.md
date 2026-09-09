# AgentCore reuse index

Use this index before implementing Harness, Gateway, Policy, approval, or demo
operations. It separates reusable proof from historical compatibility code.

## Reuse directly in this repository

| Need | Source | Use |
| --- | --- | --- |
| Harness least-tool proof | `docs/research/HARNESS_NOVA2_LITE_LIVE_PROOF.md` | Preserve explicit `allowedTools` and absence of direct Runtime commands |
| Gateway/Policy live proof | `docs/research/GATEWAY_POLICY_LIVE_PROOF.md` | Reuse exact IAM, Cedar input condition, Lambda metric, and public/private evidence boundaries |
| Cost assumptions | `docs/research/COST_MODEL_V0.md` | Update measured request, token, Lambda, log, and retained-resource costs |

## Consult the sibling AgentCore repository

Repository: `mytestlab123/AgentCore`

| File | Proven lesson | Reuse boundary |
| --- | --- | --- |
| `docs/HARNESS_MVP_PROOF.md` | Real Harness create/invoke/delete PASS in Singapore | Learn lifecycle and proof shape; do not copy account-specific evidence |
| `scripts/harness-mvp.sh` | Fixed-name Harness lifecycle and cleanup checks | Reuse validation ideas, not the historical wrapper wholesale |
| `scripts/harness_inline_tool.py` | Exact inline-tool parsing and resume contract | Use only if Pilot v1 needs client-owned inline tools |
| `docs/ISSUE31_GATEWAY_POLICY_PROOF.md` | Native Gateway ALLOW/DENY with Lambda deltas | Reuse exact proof semantics |
| `docs/AGENTCORE_CLI_GATEWAY_POLICY_LEARNINGS.md` | CLI/CDK, MCP version, IAM, Policy, metrics, retention lessons | Apply the sanitized lessons before any deployment change |

## Do not reuse wholesale

- LibreChat/OpenAI compatibility adapters;
- historical synthetic governance plumbing;
- resolved CLI/CDK state containing private identifiers;
- raw screenshots, logs, credentials, endpoints, account IDs, or ARNs.

Pilot v1 should promote the small native patterns into product-owned code and
tests under this repository.
