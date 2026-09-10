# Platform Phases 8–10 plan

Authority: Issue #20
Base: main after PR #18 merge `d44c0a339ae1ca79f63ff8adbdd18bcc800dd9ae`
Status: seed plan — implementation not started

## Outcome

Deliver the first bounded bulk-remediation path for one exact S3 compliance control while preserving deterministic scope, explicit human approval, provider verification, durable per-item state, and read-only LibreChat/MCP.

## Required preflight before implementation

Codex records two short answers in the owning PR and then continues automatically unless a genuine blocker is found.

1. Bulk preflight: inspect `vagent` identity/Region, S3 quota/utilization, account-level Block Public Access, Config recorder/rules/evaluation behavior, credits/cost visibility and material quotas. Recommend 10 / 50 / 100 / 1000 as the maximum justified live scale for this run. Create no resources during preflight.
2. Knowledge-tool check: compare existing MCPs vs Context7 Skill vs Context7 MCP on 2–3 actual repo dependencies. Select one or none. Prefer aws_knowledge for AWS docs and local runtime inspection for local failures. Do not install tools simply because they exist.

## Phase 8 — Bulk engine

- M1 immutable server-owned batch manifest, batch/item IDs and approval hash/version.
- M2 durable per-item lifecycle with restart/reconciliation and no blind replay.
- M3 1,000-item offline synthetic fixture plus paginated/filterable UI/API/export; Reject dispatches nothing.

No live bulk fleet creation in Phase 8.

## Phase 9 — Exact S3 remediation

- M4 one exact bucket-level S3 Block Public Access compliance/remediation family only.
- M5 manifest/tag-bound empty demo-bucket create/reset/cleanup utility; begin with 5–10 real `vagent` buckets after preflight.
- M6 human-approved real batch: exact preview -> Reject no-call -> new preview -> Approve -> exact BPA update -> independent per-bucket readback.

No bucket objects, policies, ACL experiments, public data, generic S3 write tool, or LibreChat execution.

## Phase 10 — Controlled scale

- M7 scale ladder 10 -> 50 -> 100 -> 1000 with cost/quota/reliability gates. 1,000 live buckets are optional; 1,000 offline items are required.
- M8 mixed failure, interruption, replay, wrong-profile/Region, manifest exclusion and stale-approval/drift proof.
- M9 integrated LibreChat read/explain -> authenticated operator approval -> deterministic batch execution -> durable per-item results -> chat readback, plus concise runbook and measured usage/cost gaps.

## Safety boundaries

- New S3 demo resources only in verified personal `vagent` lab after preflight.
- Preserve the existing `amit` deployment and do not silently switch its runtime identity.
- No company/GovTech/production accounts or data.
- Existing single-SG mutation remains unchanged.
- No SG bulk work, second S3 mutation family, generic AWS write surface, multi-account onboarding, database/workflow engine, Supervisor/A2A/Registry/Temporal Policy/EKS.
- Keep account IDs, ARNs, credentials, bucket names, raw findings and private screenshots outside public Git.

## Delivery model

One Issue + one PR for all three phases. Codex completes preflight and M1–M9 autonomously, using focused checks and one final validation/public-safety/diff batch. If live scale is blocked by cost/quota/access, finish safe offline/backend work and return the exact maximum justified live scale rather than fabricating evidence.
