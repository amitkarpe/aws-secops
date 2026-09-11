# Platform Phases 11–13 plan

Authority: Issue #22
Base: main after PR #21 merge `6c6f80722e7538eab38bb6fdc508b82ea25f2aec`
Status: seed plan only; implementation not started

## Outcome

Move the proven S3 bulk remediation flow into the normal LibreChat operator experience while keeping authorization and provider truth outside the model.

```text
LibreChat
-> exact immutable batch
-> native ASK approval
-> durable execution start
-> AgentCore Gateway
-> AgentCore Policy
-> exact S3 remediation target
-> S3 provider readback
-> durable result
-> LibreChat readback
```

The existing Operator UI remains an audit/debug fallback, not a required step for normal remediation.

## Non-blocking architecture check

Before implementation, compare Gateway target/executor options for one exact S3 BPA action:

1. Lambda target -> S3 API
2. narrow wrapper -> SSM Automation/Document -> S3 API
3. existing bounded OpenAPI/API Gateway/MCP target, if useful
4. direct Smithy/AWS-service target only if current protocol support actually fits

Use `aws_knowledge` first for current AgentCore target facts. Record one choice and continue; do not wait for Amit unless a real safety/cost/access blocker appears.

Questions to answer:
- Is SSM Automation/Document a first-class AgentCore Gateway target today?
- What wrapper, IAM role and state does SSM add here?
- Which option is smallest/least-privilege/easiest to audit for `PutPublicAccessBlock`?
- Where would SSM become preferable later?

## Phase 11 — Inline LibreChat approval

- M1: one exact execution-intent tool accepting only existing `batch_id` + immutable `approval_hash` (or equivalent exact server-owned identifiers).
- M2: native LibreChat `ask` approval; Reject gives zero dispatch; Approve means approve-and-execute exactly this frozen batch once. No session-wide Approve All.
- M3: normal remediation completes inside LibreChat; no Operator URL required. Operator UI remains available for audit/debug.

## Phase 12 — AgentCore-governed S3 execution

- M4: replace Phase 8–10 direct CLI write path with one selected exact Gateway target; no generic AWS/S3 write surface.
- M5: prove independent LibreChat Reject, AgentCore Policy DENY and Policy ALLOW outcomes. Chat approval is not AWS authorization.
- M6: provider re-read determines COMPLETED; keep DENIED/FAILED/UNKNOWN distinct and reconcile ambiguous effects without blind retry.

## Phase 13 — Durable execution + scale to 100

- M7: approval starts durable execution; browser/model connection is not the worker. Preserve one authoritative writer, restart-safe progress and no replay of terminal/uncertain items.
- M8: live scale ladder `10 -> 50 -> 100`, then STOP. Recheck cost/quota/provider readiness before each step. 1,000 live resources are out of scope; prior 1,000 offline proof is sufficient.
- M9: real LibreChat E2E: find -> explain -> request remediation -> native approval -> Policy ALLOW -> governed execution -> progress -> provider verification -> final chat summary. Also prove Policy DENY and interruption/reconciliation.

## Boundaries

Personal lab only. No company/GovTech/production data. Preserve old SG remediation. One exact S3 BPA family only. No generic mutation tool, session-wide Approve All, 1,000-live run, new scanner, multi-account onboarding, Organizations, Registry/Supervisor/A2A/Temporal/EKS, database/workflow engine or unrelated UI rewrite. Keep credentials, IDs, ARNs, bucket names, private endpoints and private screenshots out of public Git.

## Delivery

One substantial PR for M1–M9. Codex works through all three phases autonomously, keeps corrections in the same PR, and returns one final HANDOFF: CHATGPT with exact HEAD, fresh/reused evidence, final resource state, known limits and cleanup state.