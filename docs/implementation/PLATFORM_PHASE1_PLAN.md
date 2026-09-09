# Platform Phase 1 implementation plan

Status: complete — M1–M5 PASS; ready for review

Authority: Issue #9

Base: `main` after Pilot v1.1 / PR #8

## Goal

Promote the Pilot into a broader multi-source AWS SecOps workflow without broadening the proven AWS mutation boundary.

```text
source finding
-> bounded adapter
-> common finding contract
-> specialist route
-> grounded explanation
-> action eligibility
-> governed supported remediation OR plan-only
-> shared backlog / audit / export
```

## Milestones

### M1 — Platform intake API/UI

- bounded JSON/CSV upload/import through the existing loopback app;
- reuse existing size/count validation;
- no browser/model supplied filesystem path;
- imported findings join the same backlog;
- imported evidence is not treated as AWS provider verification.

### M2 — CloudSCAPE-style + VAPT-style adapters

- public-safe synthetic fixtures only;
- explicit deterministic mapping to the common finding contract;
- reject malformed/unsupported rows;
- no generic ETL framework;
- no real company/GovTech/CloudSCAPE/VAPT data in Git.

### M3 — Specialist routing

- Compliance Agent for compliance/configuration findings;
- Vulnerability Agent for VAPT/vulnerability findings;
- deterministic/server-owned routing;
- no Supervisor/A2A or model-selected arbitrary agent/tool;
- source-aware grounded explanations.

### M4 — Action eligibility + governed workflow

- existing exact unrestricted-SSH SG finding remains the only supported mutation;
- imported/unsupported findings are `PLAN_ONLY`;
- preserve human Reject, Policy DENY, DEV ALLOW, exact Lambda and provider re-read semantics;
- make `REMEDIATION_SUPPORTED` vs `PLAN_ONLY` explicit in API/UI/audit.

### M5 — Platform operations view + end-to-end proof

- show source, specialist route, severity/status, eligibility, counts/grouping and action plan;
- extend existing CSV/Markdown export only where useful;
- one proportional end-to-end smoke covering both specialist routes plus the preserved governed SG path.

## Boundaries

Do not add Organizations/StackSets, real multi-account onboarding, company/production access, live source credentials/connectors, a second AWS remediation action, generic AWS write tooling, Registry, Temporal Policy, Supervisor/A2A, multi-user auth, EKS, or large ingestion/testing/reporting frameworks.

Use only the approved personal AWS lab and public-safe synthetic source fixtures. Keep all private identities, raw evidence, company files and real security reports outside Git.

## Validation / Git economy

During implementation run only focused checks needed for the current change. Milestone commits may remain local.

At the end perform one batch:

1. deterministic tests;
2. one real API/provider smoke;
3. at most one browser smoke if the UI changed materially;
4. `git diff --check`;
5. public-safety review;
6. final diff/status review;
7. one push;
8. one evidence/handoff comment.

## Final acceptance

```text
multi-source intake
-> common contract
-> Compliance / Vulnerability routing
-> grounded explanation
-> explicit action eligibility
-> supported governed SG remediation OR plan-only
-> shared backlog / audit / export
```

The existing exact SG mutation boundary must remain unchanged.

## Result

- M1: same-origin JSON/CSV content upload is bounded to 256 KB and 100 records;
  the API accepts a basename, never a browser-supplied filesystem path.
- M2: explicit CloudSCAPE-style and VAPT-style adapters accept only their
  public-safe synthetic schemas and reject missing, extra, or unsupported data.
- M3: server-owned routing sends compliance/configuration evidence to
  `Compliance Agent` and VAPT evidence to `Vulnerability Agent`.
- M4: imported evidence is always `PLAN_ONLY`; only the provider-backed exact
  public-SSH Security Group finding is `REMEDIATION_SUPPORTED`.
- M5: the common backlog and CSV/Markdown exports show source, specialist, and
  eligibility. One live API/provider smoke and one browser-visible smoke pass.
