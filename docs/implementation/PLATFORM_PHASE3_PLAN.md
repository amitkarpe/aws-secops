# Platform Phase 3 implementation plan

Status: M1–M5 PASS — ready for review; see PLATFORM_PHASE3_PROOF.md

Authority: Issue #13

Base: `main` after Platform Phase 2 / PR #12

## Goal

Add a small durable local backlog and remediation-planning lifecycle without new AWS resources or expanding the existing mutation boundary.

```text
provider/import finding
-> stable finding identity
-> durable local backlog
-> first/last seen + occurrence tracking
-> operator mitigation plan
-> safe reconciliation
-> management export
```

## Milestones

### M1 — Stable identity + tracking metadata

Add deterministic stable finding IDs from server-owned normalized fields. Track first/last seen, occurrence count, latest-sync visibility, owner, mitigation plan, target/timeline and planned/unplanned state separately from provider compliance status.

### M2 — Minimal durable local store

Persist bounded backlog/tracking state to one small server-owned local JSON file. Keep it outside Git, ignored by Git, and use safe/atomic replacement. No database or framework.

### M3 — Safe reconciliation

Repeated Config sync/import must reuse stable IDs and preserve operator planning metadata. A missing Config record is not COMPLIANT or VERIFIED. Failed sync preserves prior durable work.

### M4 — Operator planning API/UI + export

Add one narrow same-origin action for bounded owner/mitigation/target/planning-status updates on an existing stable finding. Reflect the same data in the operations view and CSV/Markdown exports. No AWS mutation.

### M5 — Restart/reconciliation proof

Prove: live Config sync -> plan one finding -> persist -> restart -> recover same ID/plan -> re-sync -> preserve plan/update tracking -> export same item. Also prove missing item is not auto-closed, failed sync does not destroy stored work, PLAN_ONLY remains PLAN_ONLY, and no private state is committed.

## Boundaries

- Personal standalone AWS lab only; Singapore `ap-southeast-1`.
- Config activity remains read-only.
- No DynamoDB/RDS/S3 persistence, IAM/service changes, new connector, multi-account work, second remediation, generic write surface, Supervisor/A2A, Registry, Temporal Policy, EKS, ORM/database framework, or large testing framework.
- Local durable state may contain private lab evidence and must remain outside Git/PR evidence.
- Existing exact Security Group remediation remains unchanged and is the only AWS mutation capability.

## Git / validation economy

Complete M1–M5 as one cohesive 2–3 hour Codex session. Use focused checks during implementation, then one final deterministic-test/live-smoke/browser-if-useful/diff/public-safety batch and one implementation push by default. Keep corrections in the same PR.
