# Pilot v1 proof

Date: 2026-09-09

Region: Asia Pacific (Singapore), `ap-southeast-1`

Private AWS identities, ARNs, endpoints, session identifiers, and raw service
responses are retained outside this public repository.

## M1 — Compliance Agent foundation: PASS

The retained research Harness was reset as the clean Pilot v1 Compliance Agent
foundation and reached `READY` with:

- Nova 2 Lite through the replaceable model configuration;
- the compliance-only system prompt;
- configured tools `[]` and allowed tools `[]`;
- Memory disabled;
- one reasoning iteration for this no-tool acceptance call;
- no `shell`, `file_operations`, Browser, Code Interpreter, or generic AWS tool;
- no `bedrock-agentcore:InvokeAgentRuntimeCommand` permission on its role.

One native AgentCore CLI invocation returned exactly
`PILOT_FOUNDATION_OK`, made zero tool calls, and its Runtime session was stopped
afterward. The CLI summary represents the response as a serialized JSON text
envelope; the product parser unwraps only its `text` field and rejects missing
or invalid text.

Focused Python tests, compilation, and `git diff --check` passed.

## M2 — Real Security Group finding: PASS

One dedicated Pilot v1 Security Group was created in the personal lab VPC. It
is unattached and contains one intentional TCP/22 ingress rule from
`0.0.0.0/0`. The read Lambda is configured with that server-owned Group ID;
the Gateway tool accepts only `environment=dev` and cannot select another
resource, Region, role, action, or AWS API.

The exact `check_security_group` tool was added to the retained AWS-IAM Gateway
and permitted by an ACTIVE Cedar policy only for the fixed `dev` context. The
Harness allowlist contains only that exact read tool. One verbose native
AgentCore CLI invocation produced:

- exact Gateway tool calls: **1**;
- real provider result: **NON_COMPLIANT**;
- evidence: TCP/22 from `0.0.0.0/0`;
- Security Group attachments: **0**;
- AWS mutation by the read tool: **none**.

The assistant explained the provider result and ended with
`STATUS: NON_COMPLIANT`. A direct EC2 provider read independently confirmed the
rule remained present after the M2 call.

The Policy analyzer rejected an initial unconditional read permit as overly
permissive. No invocation occurred under that failed policy. The final tool,
Lambda validation, and Cedar condition all require `environment=dev`; strict
validation then reached ACTIVE without ignored findings.
