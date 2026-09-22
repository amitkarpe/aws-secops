# Issue #186 — deterministic exceptions and audit ledger

Authority: Issue #186 / PR #187; Issue #170 M4A only.

## Contract

M4A is a synthetic/local extension of the M2 1K finding store and M3B manual
selection pilot for `restricted_ssh`. It adds one strict public exception
record: exact account/control/resource, owner, reason, reference, creation and
expiry timestamps, deterministic ID, and append-only revision. There is no
wildcard target, inferred field, AWS client, or live mutation path.

An exception is never a compliance result. The finding's provider and Config
status are unchanged. A record excludes only its exact current finding while
its latest revision is `ACTIVE`; expired and revoked records remain visible but
cannot exclude.

## Integrity and approval

Before a M3B preview freezes, every selected row is re-resolved against the
current finding store and exception registry. The frozen scope includes the
canonical exception receipt/digest and applicable IDs. A later exception
create, revision, revoke, or expiry that changes that digest makes the old
batch fail closed with `re-prepare the candidate scope`.

The inherited M3A exact `batch_id + scope_hash + APPROVE/REJECT` adapter remains
the only decision boundary. The ledger cannot decide, approve, or dispatch.
Reject records the native decision and dispatches no synthetic executor. An
Approve runs only the existing `NoopExecutor`, exactly once per eligible row;
replays are blocked and recorded. No live AWS write exists in this pilot.

## Audit and operator boundary

The logical ledger is append-only and hash chained, with deterministic
sequence/timestamp ordering for synthetic tests. It can use an operator-owned
append-only JSONL backing file and verifies the complete hash chain on reopen.
It records discovery/candidate
intake/manual selection, exception resolution, preview/freeze, native decision,
synthetic dispatch/result, provider verification, Config convergence, exports,
and blocked replay/decision attempts. Provider readback and Config convergence
remain distinct event types.

Only bounded exception/audit pages and summaries are suitable for model context.
Full CSV/JSONL exports are backend-generated and represented to callers by a
digest receipt; export contents must not be placed in model context.

## Validation

```bash
python3 -m unittest -v tests.test_issue186_exceptions_audit
bash scripts/check.sh
```

The focused suite proves exact active exclusion, expiry/revoke non-exclusion,
revision history, changed exception state requiring re-prepare, Reject zero
dispatch, exact partial synthetic Approve, replay audit evidence, distinct
provider/Config events, bounded views, and backend export receipts.

## Out of scope

No M4B control expansion, private catalog data, live AWS mutation, IAM/OIDC or
network changes, new approval engine, generic model execution surface, or work
on the independent Issue #176 / PR #177 track.
