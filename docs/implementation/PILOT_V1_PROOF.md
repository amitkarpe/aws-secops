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
