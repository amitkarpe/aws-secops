# Issue #180 — deterministic 1K query and export

Authority: Issue #180; Issue #170 M2.

## Contract

The compact fixture produces 50 synthetic aliases (`lab-001` through
`lab-050`), 20 findings per alias, and exactly 1,000 findings. Each of the four
generic controls has 250 findings. Every fifth finding per alias/control has a
synthetic one-time exception, producing 200 exceptions and 800 non-exceptions.
No live AWS account or private catalog record is used.

`ScaledFindingStore` owns the complete backend truth. Its model-facing API
returns only:

- aggregate fleet/control/status/exception counts;
- one filtered, searched, deterministically sorted page capped at 100 rows; or
- an export receipt containing row count, filename, and SHA-256 digest.

Search is limited to account alias, generic control key, resource type, and
synthetic resource ID. Exact filtered counts are calculated before pagination.
Invalid filters, sort keys, pages, and limits fail closed; an out-of-range valid
page returns an empty page with the exact total preserved.

## CSV boundary

The CSV backend uses the same filter and sort implementation as page queries.
It emits only the fixed public columns documented by Issue #180, with stable
column order and spreadsheet-formula neutralization. CSV content is a backend
artifact and is not included in the MCP/model response. The model receives only
the export receipt.

## Safety

- read-only synthetic data; no AWS calls or credentials;
- no account IDs, ARNs, private mappings, or raw private findings;
- no IAM, OIDC, networking, approval, executor, or remediation changes;
- no bulk selection or Issue #170 M3 behavior;
- existing capability ceilings remain unchanged.

## Validation

Run the focused acceptance:

```bash
python3 -m unittest -v tests.test_issue180_scaled_findings
```

Run the complete repository regression:

```bash
bash scripts/check.sh
```

Representative local timings are recorded in the PR handoff from the exact
review head; they are observations rather than performance budgets.

On the development host, 200 in-process repetitions over the deterministic
1K truth produced these observations (median / p95):

| Operation | Median | p95 |
| --- | ---: | ---: |
| unfiltered 100-row page | 0.201 ms | 0.242 ms |
| filtered 100-row page | 0.054 ms | 0.068 ms |
| account/control search page | 0.026 ms | 0.030 ms |
| full 1,000-row CSV | 3.389 ms | 4.420 ms |
| filtered 250-row CSV | 0.803 ms | 0.890 ms |

These measurements include only local generation/query/serialization and are
not a network or hosted-runtime service-level objective.
