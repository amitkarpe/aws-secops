# Issue #182 — CSV candidate-scope pilot

Authority: Issue #182; Issue #170 M3A only.

## Trust boundary

CSV is an untrusted candidate list, not finding evidence, approval, or mutation
authority. The strict intake accepts exactly these public fields:

```text
account_alias,control_key,resource_id
```

It is UTF-8-only, bounded to 128 KB and 1,000 rows, normalizes only surrounding
whitespace, rejects formula-prefixed values, and requires exact headers. It
does not interpret cell values as instructions.

Every unique candidate is independently re-resolved against the deterministic
M2 server-owned truth. The M3A pilot permits only `restricted_ssh`. The preview
classifies every submitted row as `ELIGIBLE`, `DUPLICATE`, `STALE`, `UNKNOWN`,
`UNSUPPORTED`, or `EXCLUDED`; exception rows are excluded from the candidate
scope. Only `ELIGIBLE` rows can enter a frozen batch.

## Frozen batch and approval

The frozen scope binds the sorted exact eligible finding/resource identities,
exclusions, selected aliases, candidate digest, evidence version/digest, and
scope hash. A unique preparation revision makes every new preview a new batch,
while canonical sorting means CSV row order cannot alter scope selection.

`decide(batch_id, scope_hash, decision)` is a server-side adapter for the
existing native Approve/Reject semantics. It accepts no wildcard or model chosen
scope. A changed evidence digest requires re-prepare; rejected, completed, and
partial batches cannot be replayed.

The only executor is `NoopExecutor`, a deterministic test double with no AWS
SDK/client. Reject produces zero dispatches. Approve dispatches exactly the
frozen eligible rows once, records per-row `NOOP_SUCCEEDED` or `FAILED`, and
does not retry. Synthetic execution status is distinct from AWS service
verification and Config convergence.

## Result boundary

`result_csv` generates full public-safe per-row detail from server-owned batch
state. Normal model-facing output contains only compact counts, a rejected row
sample capped at 100, and a CSV receipt (filename, row count, digest); it never
contains the complete candidate or result CSV.

## Validation

```bash
python3 -m unittest -v tests.test_issue182_csv_bulk_pilot
bash scripts/check.sh
```

The focused suite proves strict intake, all preview classes, canonical frozen
scope, stale-evidence re-prepare, Reject zero dispatch, exact no-op Approve,
explicit partial failure, replay prevention, and deterministic result export.

## Out of scope

No live AWS mutation, IAM/OIDC/network changes, generic model execution tool,
new approval system, new control, private catalog data, or Config-GUI M3B work
is included.
