# Compliance Agent v1

Status: **VERIFIED — release publication pending (Issue #125)**

Owning Issue: #123

## Purpose

Compliance Agent v1 is a clean specialist agent for the current four-account AWS compliance demo.

It is intentionally isolated from the legacy Compliance Agent implementation.

## Isolation rules

Implementation will live under this directory on a fresh implementation branch.

Do not:

- import `pilot_v1/compliance_mcp.py`;
- call the retired Operator backend on port 4444;
- reuse the retained 100-S3 / 10-SG legacy agent path;
- rename legacy code and treat it as v1.

The new agent will use the unified Config backend and current four-account contracts.

**Agent layer:** Amazon Bedrock AgentCore Harness is the intended primary reasoning/tool runtime for Compliance Agent v1. LibreChat is the frontend/client, not the source of agent truth.

This corrects the current split architecture: the repository already proved a live read-only AgentCore Harness operator, while the broken LibreChat Compliance Agent followed a separate legacy path to retired port 4444.

## v1 scope

Exactly four aliases:

- `lab-dev`
- `lab-poc`
- `lab-qa`
- `lab-sec`

Exactly two controls:

- `s3-bucket-level-public-access-prohibited`
- `restricted-ssh`

Verified capabilities:

- current status;
- finding explanation;
- bounded remediation plan;
- operational detail, including account/resource identifiers when the authorized backend provides them;
- preserved approval/security boundary;
- automated backend/MCP/AgentCore Harness acceptance;
- programmatic golden-prompt invocation against Harness;
- minimal LibreChat browser smoke.

## Implementation layout

```text
agents/compliance-agent-v1/
  README.md
  RELEASE_NOTES.md
  src/
  prompts/
  harness/
  tests/
```

Implementation now lives in this isolated v1 line; legacy port 4444 and `pilot_v1.compliance_mcp` remain excluded.

## Identifier handling

Compliance Agent v1 does not use alias-only privacy masking as an acceptance requirement.

- Return account/resource identifiers when they are supplied by an authorized backend/tool and help operations.
- Do not invent identifiers that the backend does not provide.
- Never expose credentials, secrets, tokens, auth/session material or unrelated private data.


## Operational history vs memory vs RAG

Compliance Agent v1 should start with a structured operational event ledger, not RAG.

- Exact change history — who, what resource, when, before/after, approval, provider verification — belongs in structured events.
- KISS v1 storage: one JSON event object per change in S3. Move to DynamoDB only when query volume/indexing needs justify it.
- AgentCore Memory is for conversation/session/episodic memory, not authoritative operational audit.
- Bedrock Knowledge Bases/RAG should be added later for runbooks, SOPs, policies, architecture docs and incident narratives when semantic document retrieval becomes useful.
- CloudTrail remains deeper AWS-native evidence, but the normal agent should be able to answer known agent-mediated change history from the structured ledger first.


## v1 implementation architecture

```text
LibreChat: Compliance Agent v1
   -> one read-only MCP tool: ask_compliance_agent_v1
   -> strict loopback Config adapter (:1111)
   -> authoritative 4-account evidence packet
   -> dedicated AgentCore Harness: compliance_agent_v1
   -> Nova 2 Lite reasoning, no tools
   -> answer back to LibreChat
```

The Harness is deliberately **tool-free** in v1. Current AWS evidence is fetched
deterministically by the local adapter before inference. This prevents the model
from selecting a generic AWS/tool surface while still making AgentCore Harness
the reasoning layer.

The adapter fails closed unless all four registered aliases and both supported
controls are present as exactly eight account/control checks.

### Runtime dependencies

- Python 3.12+
- latest compatible boto3 with AgentCore `InvokeHarness`
- MCP Python SDK
- existing EC2 instance role with exact `bedrock-agentcore:InvokeHarness`
  permission for the dedicated v1 Harness only

### Live acceptance

Run `compliance_agent_v1.acceptance` against the dedicated Harness ARN. It
checks status, explanation, no-change planning, explicit-fix boundary, and
identifier fidelity before LibreChat smoke testing.


## Verification status — 2026-09-20

- Config backend: PASS (4 aliases × 2 controls = 8 checks)
- AgentCore Harness golden prompts: PASS 5/5
- read-only / no-mutation boundary: PASS
- installed MCP bridge startup and invocation: PASS
- LibreChat agent registration: PASS
- GitHub regression CI: PASS (run 236)
- verified commit: `8779cf9bd771be296b7983bf20e3881de3e10e48`

Not yet claimed:
- authenticated LibreChat UI/API smoke;
- published GitHub Release `compliance-agent-v1.0.0`.

