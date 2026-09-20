# Governance

The central rule is:

> **The model is an assistant, not the authorization boundary.**

## 1. Compliance Agent v1 is read-only

The clean v1 path has two deterministic boundaries before model reasoning:

1. the loopback Config adapter accepts only the exact four registered aliases and two controls;
2. the dedicated AgentCore Harness has no tools.

LibreChat exposes exactly one v1 MCP tool:

`ask_compliance_agent_v1`

That tool gathers current evidence first, invokes the Harness for bounded reasoning, and returns `mutation=false`.

An operator saying `fix`, `apply` or `execute` does not create v1 mutation authority.

## 2. Prompt intent is not authorization

Instructions help classify read, explain, plan and execution intent, but text is never an AWS security boundary.

Compliance Agent v1 has no executor.

The separate governed mutation path additionally requires:

- supported control;
- server-owned exact scope;
- frozen batch identity;
- native human decision;
- fixed CodeBuild/G/O path;
- exact registered target sessions;
- provider verification.

## 3. Evidence claims are bounded

The agent may state only what current evidence supports.

Examples:

- Config `NON_COMPLIANT` is a Config finding, not proof of public exposure, sensitive data, attacker activity or exploitability.
- Missing resource/account identifiers remain unavailable; they are never fabricated.
- Config is asynchronous evidence and does not prove a provider mutation succeeded.
- Provider success requires direct provider readback from the governed execution path.

## 4. Fail closed

The v1 adapter rejects incomplete scope:

- wrong/missing aliases;
- missing controls;
- duplicate/unexpected checks;
- partial/unavailable Config evidence;
- unhealthy Config provider.

The Harness client rejects malformed responses, runtime errors and unexpected tool-use events.

## 5. Strict MCP boundary

The v1 MCP argument model rejects unexpected/coerced arguments.

The server exposes no generic shell, AWS CLI/API or arbitrary resource selector.

## 6. Human approval is separate

The governed mutation path keeps S3 and restricted-SSH decisions separate.

Approval means only:

> **This exact frozen supported batch may proceed to the bounded executor.**

It does not prove the provider changed.

Reject means zero dispatch for that exact request.

## 7. Provider verification

After an approved mutation, AWS is read again.

Only matching direct provider state can establish completion. AWS Config may converge later.

## 8. Operational history, memory and RAG

Keep these concepts separate:

- structured operational event history — exact who/what/when/before/after/approval/provider verification;
- AgentCore Memory — conversational/episodic continuity;
- Knowledge Bases/RAG — future semantic retrieval across runbooks, SOPs, policies and incident narratives.

Memory/RAG do not replace authoritative operational evidence.

## Public safety

This repository is public. Never publish credentials, tokens, account/session secrets, private auth material, raw private findings or private screenshots.
