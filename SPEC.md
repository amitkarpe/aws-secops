# Specification

Status: implemented and validated — Phases 5–7 / Issue #17 / PR #18; ready for review

## Problem

Extend the proven Compliance Agent into a bounded multi-source AWS SecOps
workflow while retaining one exact governed AWS mutation.

## Scope

### Approved named UI entry points — 2026-09-10

Amit selected option 1: reuse the retained EC2 with one reverse proxy and TLS,
preserve the legacy AgentCore DNS/service, add separate chat/operator subdomains,
and protect the Operator UI with its own login. Scoped DNS, certificate renewal
IAM, HTTPS ingress restricted to the existing trusted source, port handoff and
service restart are approved. Operator backend stays loopback-only; the proxy
must reject cross-origin writes before translating trusted upstream headers.
Use the same PR #18; validate with Playwright and notify ChatGPT. No AWS approval
may be inferred from chat access. Credentials and deployment names stay private.

### Amit approval amendment — 2026-09-10

Amit approved completing this release using the home Linux host or reusing
the retained EC2; creating a suitable personal-lab EC2 is also authorized when
reuse is insufficient. Scoped hosting, IAM, private connectivity, installation,
deployment and restart steps needed by this Issue are approved without another
routine permission request. This supersedes the original no-new-IAM/resources
restriction for deployment prerequisites, not the application mutation boundary.
Use `amit` / `ap-southeast-1` for the retained implementation. `vagent` is an
approved alternative, not an automatic fallback: verify its separate identity,
Region, available services/quota and cost before using it. Prefer reuse to new
recurring cost. Keep credentials/private evidence out of Git, avoid public
operator exposure, and preserve unrelated services, chats and user work.

Preserve merged Phase 4 and deliver Issue #17: bounded backend queries,
inference-independent intake, cached zero-tool explanations, restricted MCP,
real LibreChat integration and exact human-review links. Deliver all nine
milestones in PLATFORM_PHASE5_7_PLAN.md. Chat cannot save plans, create jobs,
approve, reject, execute or rearm. No second AWS mutation capability.

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

- No unrelated AWS resources, IAM or service enablement. Scoped deployment
  prerequisites are authorized by the amendment above; prefer the retained EC2.
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
  of private data, risk to a non-demo resource, or expansion beyond Issue #17.
