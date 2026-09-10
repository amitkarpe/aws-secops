# Platform Phase 2 implementation plan

Status: complete — M1–M5 PASS; PR #12 ready for review

Authority: Issue #11

Base: `main` after Platform Phase 1 / PR #10

## Goal

Add exactly one live AWS provider-native finding source to the existing multi-source SecOps platform, read-only, without widening the proven mutation boundary.

```text
live AWS provider source
-> bounded read-only fetch
-> explicit adapter
-> common finding contract
-> deterministic specialist route
-> grounded explanation
-> provider provenance/freshness
-> shared backlog/export
```

## Milestones

### M1 — Read-only provider preflight and selection

Privately verify AWS identity and `ap-southeast-1`, then inspect AWS Config, Inspector, and Security Hub in that order. Select exactly one source already usable without service enablement, resource creation, IAM change, or other AWS mutation. If none is usable, stop `BLOCKED_SOURCE_UNAVAILABLE` on PR #12 rather than enabling anything.

### M2 — Exact provider adapter

Implement one small explicit adapter for the selected source. Bound results to the existing finding limit and normalize only the fields needed by the common finding contract. Do not build a generic ETL/AWS execution framework.

### M3 — Live source sync

Add one server-owned read-only sync path through the existing loopback API/UI. The browser/model must not select arbitrary AWS APIs, Regions, accounts, or resources. Route deterministically to the existing specialist workflow. Add no mutation tool.

### M4 — Provenance, freshness and operations view

Show provider source, observed/sync time, provider-backed vs imported evidence, specialist route, severity/status, eligibility, and source success/error state where useful. Keep the same backlog and existing CSV/Markdown export as the source of truth.

### M5 — Proportional end-to-end proof

Prove one real live provider sync -> normalization -> specialist route/explanation -> provenance/freshness -> backlog/export. The new source remains PLAN_ONLY unless an existing exact SG eligibility rule already applies. Run focused tests, one live provider/API smoke, at most one browser smoke if the UI materially changes, `git diff --check`, and public-safety review.

## Boundaries

- Personal standalone AWS lab only; Region `ap-southeast-1`.
- New Phase 2 integration is read-only.
- No service enablement/configuration, new AWS resources, IAM changes, second remediation action, generic AWS write surface, multi-account onboarding, Supervisor/A2A, Registry, Temporal Policy, EKS, or large framework.
- Never commit account IDs, caller ARNs, credentials, endpoints, raw private findings, or unnecessary live resource identifiers.
- Existing exact Security Group mutation remains the only supported AWS mutation.

## Git / validation economy

Delivered: Config was the first usable source in live preflight. One bounded
read-only adapter and server-owned sync now feed Compliance Agent through the
retained zero-tool Harness path. Provenance, timestamps and source health are
visible in the existing UI and exports. See `PLATFORM_PHASE2_PROOF.md`.

Codex completes M1-M5 as one cohesive 2-3 hour worker session. Use focused checks during implementation, then one final validation/Git batch and one push by default. Use Issue #11 / PR #12 as the durable handoff; Amit should not copy/paste worker state.
