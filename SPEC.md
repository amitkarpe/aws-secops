# Specification

Status: complete — Platform Phase 1 / Issue #9 ready for review

## Problem

Extend the proven Compliance Agent into a bounded multi-source AWS SecOps
workflow while retaining one exact governed AWS mutation.

## Scope

Preserve Pilot v1.1 and deliver Issue #9 M1–M5: bounded source intake, two
explicit adapters, two deterministic specialist routes, explicit action
eligibility, and the shared operations view/export.

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
- Keep the provider-backed exact public-SSH Security Group finding as the only
  `REMEDIATION_SUPPORTED` record.

## MUST NOT

- Do not add generic AWS actions, arbitrary resource selection, multi-user auth,
  multi-account support, Registry, Temporal Policy, EKS, Supervisor, or A2A.
- Do not use company, production, or Organizations-management resources.
- Do not commit account IDs, ARNs, endpoints, session IDs, credentials, or raw
  private evidence.

## Verification

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
  of private data, risk to a non-demo resource, or expansion beyond Issue #9.
