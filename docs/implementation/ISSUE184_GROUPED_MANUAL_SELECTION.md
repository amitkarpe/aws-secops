# Issue #184 — grouped/manual selection pilot

Authority: Issue #184; Issue #170 M3B only.

## Selection contract

M3B is a synthetic/local `restricted_ssh` operator pilot. It reuses the M2
deterministic finding store and the M3A frozen batch, native decision, no-op
executor, and result-export implementation.

The server owns the selection as an exact set of current `finding_id` values.
Operators can request a bounded filter/sort/page view and group counts by
account alias or control key. Those operations are read-only views: none can
add, remove, widen, or shrink selection. Explicit add/remove is required for
manual selection. An unknown, stale, or unsupported ID cannot be added.

`select_all_current_filter` resolves and records the exact current filtered
server-side ID set. It is not a wildcard, does not select hidden rows, and does
not include future findings. The compact receipt contains only selection count
and digest; complete IDs remain server-side.

## Preview and freeze

Before freeze, the saved IDs are re-resolved against current backend truth and
classified as `ELIGIBLE`, `STALE`, `UNKNOWN`, `UNSUPPORTED`, or `EXCLUDED`.
The M3A shared freezer binds the sorted exact eligible IDs/resources, selected
accounts, exclusions, selection digest, evidence version/digest, scope hash,
and unique batch identity. No eligible rows means no frozen batch. A changed
evidence digest requires re-prepare.

The inherited exact `batch_id + scope_hash + APPROVE/REJECT` decision adapter
remains the only approval semantics in this synthetic pilot. Reject dispatches
nothing. Approved batches invoke only the test-only `NoopExecutor` once per
eligible row. Results are per-row and terminal batches cannot replay. No AWS
client, generic model execution tool, or live mutation exists in this path.

## Compact result boundary

The Config-style response contains group counts, one bounded page, selection
count/digest, preview counts, bounded rejected sample, frozen state, and result
summary. Full row detail is backend-generated CSV plus an export receipt; it is
not inserted into model context.

## Validation

```bash
python3 -m unittest -v tests.test_issue184_grouped_selection
bash scripts/check.sh
```

The focused suite proves page/sort/group invariance, exact add/remove, filtered
select-all materialization, re-resolution classes, freeze/re-prepare, Reject
zero dispatch, exact no-op Approve, and deterministic result export.

## Out of scope

No live AWS mutation, IAM/OIDC/networking, new controls, new approval engine,
generic model execution, private catalog data, or Issue #170 M4 work.
