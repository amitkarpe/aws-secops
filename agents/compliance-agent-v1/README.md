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
- automated backend/MCP/agent acceptance harness;
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
