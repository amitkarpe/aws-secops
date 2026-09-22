# Issue #188 — governed synthetic `s3_ssl` expansion

Authority: Issue #188 / PR #189; Issue #170 M4B only.

## Contract

This local/synthetic milestone promotes exactly `s3_ssl` as the second governed
control alongside `restricted_ssh`. The existing M2 1K finding store already
owns deterministic public S3 bucket findings. M4B reuses the existing grouped
selection, frozen scope hash, native decision, managed exception registry,
append-only audit ledger, synthetic no-op executor, and backend result export.

The public capability record makes `s3_ssl` PREPARE/REMEDIATE/VERIFY support
explicit and requires human approval plus provider verification. It remains
routing metadata only: `execution_authorized` is always false. `s3_logging`
and `s3_backup` remain read-only EXPLAIN capabilities; no third control exists.

## Cross-control integrity

Every pilot has one explicit control. It rejects an attempt to add a row for
the other control. A mixed selected scope is not silently narrowed: it becomes
`NO_ELIGIBLE_CANDIDATES` with `MIXED_CONTROL_SCOPE_REQUIRES_SEPARATE_BATCHES`.
Operators must explicitly create separate exact batches.

Exception records include the exact control and resource prefix. An active SSH
exception cannot exclude an S3 finding, and an active S3 exception cannot
exclude SSH. The control, selected exact rows, evidence receipt, and exception
receipt all remain part of the frozen scope hash.

## Approval, audit, and operator boundary

Reject records the exact native decision and dispatches no executor. Approve
can run only the inherited `NoopExecutor`, exactly once for the frozen rows of
the one selected control. It has no AWS client and reports `aws_mutation=false`.
Replay is blocked and recorded. Provider verification and Config convergence
remain distinct read-only audit events.

The compact operator receipt is control-bound and contains only result counts,
active exception count, audit timeline, and backend export receipts. Complete
CSV/JSONL exports remain backend-side and are never model context.

## Validation

```bash
python3 -m unittest -v tests.test_issue188_s3_ssl_governed_expansion
bash scripts/check.sh
```

The M4B suite proves capability non-authority, selection isolation, mixed scope
failure, control-bound exceptions, different control scope hashes, Reject zero
dispatch, exact synthetic S3 Approve rows, and bounded audit/result exports.

## Out of scope

No live AWS mutation, IAM/OIDC/network changes, private catalog mappings,
generic remediation engine, new approval/exception/audit implementation, third
control, or work on Issue #176 / PR #177.
