# Specification

Status: complete — Platform Phase 4 / Issue #15 ready for review

## Problem

Extend the proven Compliance Agent into a bounded multi-source AWS SecOps
workflow while retaining one exact governed AWS mutation.

## Scope

Preserve the merged Phase 3 backlog and deliver Issue #15: durable jobs for
the existing exact provider-backed DEV public-SSH remediation, action preview,
single-use human decision, retained Policy/Lambda execution, independent
verification and restart-safe audit. No second AWS mutation capability.

## MUST

- Use Nova 2 Lite through AgentCore Harness in `ap-southeast-1`.
- Keep Harness built-ins unavailable and expose only exact Gateway tools.
- Ground the SG and S3 results in current AWS provider reads.
- Require a human decision before the exact SG remediation.
- Prove Reject and Policy DENY make zero changes.
- Re-read AWS after approval and report COMPLIANT only from provider truth.
- Keep the UI single-user, compact, and manager-readable.
- Record sanitized live evidence, costs, retention, and cleanup commands.
- Keep finding import at 100 records/256 KB and S3 assessment at five
  server-owned buckets; caller/model-selected buckets are prohibited.
- Derive management totals and exports from the same deterministic findings.
- Accept only same-origin JSON/CSV content uploads capped at 256 KB and 100
  records; do not accept a browser/model-supplied filesystem path.
- Treat imported CloudSCAPE/VAPT evidence as `PLAN_ONLY`, never as AWS provider
  verification or authorization to mutate.
- Route specialist work deterministically on the server; do not let a model
  select an arbitrary agent or tool.
- Imported explanations use distinct server-owned specialist instructions via
  the retained Nova 2 Lite Harness, with zero effective tools and rejection of
  any attempted tool call.
- Keep the provider-backed exact public-SSH Security Group finding as the only
  `REMEDIATION_SUPPORTED` record.

## MUST NOT

- No new AWS resources, IAM, service enablement or configuration in Phase 4.
- Only the retained dedicated demo SG and exact action may be exercised live,
  including rearm to the approved unattached demonstration state.
- A pending job is consumed durably before network execution. Terminal jobs
  cannot be replayed. Interrupted execution becomes FAILED with unknown effect;
  no automatic retry. Only independent matching provider COMPLIANT can finish
  an allowed action as COMPLETED. Generic tool errors are not Policy DENY.
- Retain at most 100 jobs/256 KB in a private atomic local journal next to the
  backlog. Plans and Config/imported findings cannot authorize a job.
- Config evaluations stay PLAN_ONLY. Do not infer fresh resource compliance
  from a recent sync or missing record; show actual observation and sync times.
- Store at most 100 findings in one atomically replaced local JSON file outside
  Git. Reject corrupt/unreadable stores without overwriting them. One app process
  owns a store; no database or multi-writer coordination is introduced.
- Derive IDs and sighting metadata on the server, independently from model text.
  Preserve operator plans during sync/import; missing bounded-snapshot records
  remain unresolved. Planning cannot alter compliance, eligibility or approvals.
- Accept only bounded owner/mitigation_plan/target/planning_status fields for an
  existing server finding ID through the existing same-origin JSON boundary.

- Do not add generic AWS actions, arbitrary resource selection, multi-user auth,
  multi-account support, Registry, Temporal Policy, EKS, Supervisor, or A2A.
- Do not use company, production, or Organizations-management resources.
- Do not commit account IDs, ARNs, endpoints, session IDs, credentials, or raw
  private evidence.

## Verification

- Phase 3: stable ID/plan survives actual process restart and Config resync;
  exports agree. Missing records stay unresolved; failed sync/write preserves
  state; corrupt store stops; planning cannot invoke AWS or expand eligibility.

- Pilot v1.1 M1–M5 focused checks and live proofs pass.
- The final visual path shows real finding, decision, Policy result, exact
  action, and provider verification.
- The S3 view is allowlisted, bounded, read-only, and provider-backed.
- Backlog totals and action-plan exports use the same validated finding set.
- Both synthetic adapters, both specialist routes, and plan-only mutation
  rejection pass through the real loopback API before the governed SG proof.
- `git diff --check` and the public-safety scan pass.

## Stop Gates

- Stop for identity or Region mismatch, unclear/unbounded recurring cost,
  ambiguous retained-resource ownership, Policy not in ENFORCE mode, exposure
  of private data, risk to a non-demo resource, or expansion beyond Issue #15.
