# Compliance Agent v1

Status: **PLANNED — not implemented or released**

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

Planned capabilities:

- current status;
- finding explanation;
- bounded remediation plan;
- operational detail, including account/resource identifiers when the authorized backend provides them;
- preserved approval/security boundary;
- automated backend/MCP/AgentCore Harness acceptance;
- programmatic golden-prompt invocation against Harness;
- minimal LibreChat browser smoke.

## Planned implementation layout

```text
agents/compliance-agent-v1/
  README.md
  RELEASE_NOTES.md
  src/
  prompts/
  harness/
  tests/
```

No implementation belongs in this planning PR.

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
