# Phase 0B.3 — Harness to Gateway Policy live proof

Status: **PASS**

Date: 2026-09-09

Region: Asia Pacific (Singapore), `ap-southeast-1`

The local `amit` profile was selected by Amit because `vagent` quota was still
pending. Identity and Region were verified before mutation; private resource
identifiers are deliberately excluded from this public repository.

## Proven path

```text
retained Nova 2 Lite Harness
        |
        v
AWS-IAM AgentCore Gateway
        |
        v
ENFORCE Policy
  dev  -> ALLOW -> exact Lambda invoked once
  prod -> DENY  -> Lambda invocation delta zero
```

The retained Harness exposes exactly one Gateway tool. Its earlier empty
allowlist was replaced with an exact allowlist for that tool; `shell` and
`file_operations` remain unavailable. The Harness role still has no
`bedrock-agentcore:InvokeAgentRuntimeCommand` permission.

## DEV — ALLOW

One native Harness invocation asked for `check_demo_scope` with
`environment=dev`.

| Evidence | Result |
| --- | --- |
| Model tool call | exact Gateway target and `check_demo_scope` |
| Tool input | `environment=dev` |
| Policy result | allowed |
| Lambda result | `HARMLESS_LAMBDA_OK`, `environment=dev`, `effect=none` |
| Assistant marker | `DEV_ALLOW_OK` |
| Lambda invocation delta | **1** |
| Model usage | 2,089 input, 43 output tokens |
| Lambda duration | 1.82 ms; 96 ms billed at 128 MB |

## PROD — DENY

One native Harness invocation asked for the same exact tool with the synthetic
input `environment=prod`.

| Evidence | Result |
| --- | --- |
| Model tool call | exact Gateway target and `check_demo_scope` |
| Tool input | `environment=prod` |
| Policy result | denied by default because no permit applies |
| Tool result | execution denied by Policy |
| Assistant marker | `PROD_DENY_OK` |
| Lambda invocation delta | **0** |
| Model usage | 2,095 input, 42 output tokens |

CloudWatch's Lambda `Invocations` metric reported exactly one invocation over
the bounded test window, matching the DEV call and proving the PROD denial did
not reach the backend.

## Authorization boundaries

- Gateway authentication is AWS IAM.
- The Harness role can invoke only the retained Gateway.
- The Gateway role can invoke only the exact Lambda and query/authorize against
  the exact Policy engine and Gateway.
- The final Gateway role policy contains zero wildcard resources.
- Cedar permits only the exact action, exact Gateway and `dev` input. Other
  input is denied by default.
- Lambda independently accepts only `dev` and performs no external action.
- The Gateway execution-role trust was tightened to the owning account and
  exact Gateway after creation.

The first Cedar version named the base IAM role as the principal. Harness uses
an assumed workload identity, so Policy-filtered tool discovery hid the tool.
That diagnostic run made no Gateway or Lambda call and was not counted as a
PASS. The corrected policy accepts any already AWS-IAM-authenticated principal,
while IAM still restricts invocation to the exact Harness role and Gateway.

## Retained resources

The dedicated Harness and its role were reused. One Gateway, one target, one
Policy engine, one Policy, one harmless Lambda, and their two dedicated roles
remain for the next experiment. All taggable resources carry experiment and
TTL ownership tags. Policy and Gateway-target APIs do not expose resource
tagging, so they are owned through their tagged parent resources. Lambda log
retention is one day. No active invocation session was intentionally retained.

These resources have no always-on compute. They are retained because the next
bounded experiment can reuse them; charges remain request-, model-, and
log-usage based.

## Measured cost

The failed diagnostic plus DEV and PROD calls used 4,262 input and 114 output
Nova 2 Lite tokens. At the Phase 0B.1 rates, model cost was approximately
**$0.00213388**. Two Gateway invocations and two Policy authorization requests
added approximately **$0.000060**. The single 96 ms, 128 MB Lambda invocation
adds about **$0.0000004** before free tier.

Total measured variable cost was therefore approximately **$0.00219428**, plus
negligible log storage. One indexed tool is approximately **$0.0002/month**.
Harness, IAM, Gateway, Policy and Lambda have no separate idle compute charge.

## AWS mutation record

This experiment created only the dedicated roles, Lambda, Policy engine,
Gateway, target and Policy described above; updated the retained Harness tool
configuration; and invoked the bounded path. Bootstrap failures created no
duplicate Gateway or target. A temporary wildcard was needed only because the
Gateway ARN does not exist before `CreateGateway`; it was immediately replaced
with the exact ARN and the final policy was verified wildcard-free.

Private raw responses, log events and resource identities are retained outside
the public repository in the local evidence directory.

## Single next experiment

Run a fixed security-task quality benchmark through the retained Harness using
Nova 2 Lite and one stronger Nova model, with the same prompt, no tools, measured
tokens/latency/cost, and a small deterministic scoring rubric. This tests the
remaining model-quality assumption without expanding the governed tool surface.

## Official sources

- [Harness tools and Gateway configuration](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-tools.html)
- [Use a Gateway with Policy](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/use-gateway-with-policy.html)
- [Add a Lambda target to Gateway](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-add-target-lambda.html)
- [Policy IAM permissions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-permissions.html)
- [AgentCore pricing](https://aws.amazon.com/bedrock/agentcore/pricing/)
- [AWS Lambda pricing](https://aws.amazon.com/lambda/pricing/)
