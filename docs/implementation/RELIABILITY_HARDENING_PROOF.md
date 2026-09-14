# Reliability hardening: scope and reproducible evidence

**Work item:** [Issue #32](https://github.com/amitkarpe/aws-secops/issues/32)
**Source baseline:** `f8afcf1abe1747ed67415c8f97ba1e90f6740ba9` (PR #31)
**Deployment status:** code/offline validation only; no AWS rollout or live remediation performed for this review.

This is a focused correction of findings in the public-release review, not a new architecture or proof of production readiness.

## Baseline and reproduction

The retained baseline workflow at `ea07aa5fbc07f0c6f178eb9a6df201493350dbb6` changed CI only. Its [GitHub Actions run](https://github.com/amitkarpe/aws-secops/actions/runs/34766989759) ran **101 tests successfully** with the pinned Boto3/MCP dependencies and Python 3.13. It also passed JavaScript syntax checks.

New regression cases were exercised against the old code before the correction. They exposed unbounded empty Config continuation pages, repeated-token acceptance, unhealthy-recorder planning reads, stranded SG approvals, reconciliation during active work, and worker-launch failure. The finite fake-client watchdog prevents the old pagination bug from hanging the test runner.

## Corrected behavior

### Config evidence

Reads of either supported rule require a healthy recorder. At most **10 evaluation-page requests / 250 results** are accepted per rule read. Legitimate empty pages may continue. A page/item ceiling yields `partial=true`; malformed/repeated/cyclic continuation tokens raise an error. Normal planners already refuse partial evidence. Operator cards now mark partial Config evidence explicitly while retaining independent provider/batch metrics.

These are application budgets, not AWS quotas or a fixed response-time promise. Existing SDK request timeouts/retry limits still apply. No recorder, rule, delivery bucket, or IAM change is made.

### SG interrupted work

The chosen recovery is **safe terminalization**, not automatic continuation.

| Item at interruption | Recovery state | May the old approval dispatch it? |
|---|---|---|
| RUNNING | UNKNOWN, effect uncertain | No; read-only reconciliation first |
| APPROVED but unclaimed | FAILED, changed=false, not dispatched | No; old approval remains consumed |
| COMPLETED / SKIPPED / DENIED / FAILED | Preserved | No terminal replay |

On an uncertain worker outcome, already in-flight calls finish before unclaimed items are expired. Each family refuses reconciliation while its own worker or an item is still running. A failed reconciliation read leaves UNKNOWN; a successful read proves present state, not who changed it.

When no uncertain/active item remains, the existing owner-operated **full-manifest** preview path can archive the old journal and create a new PENDING batch, subject to its guards and version budget. Fresh execution requires a new approval and the unchanged Gateway/Policy route. Already compliant resources can be skipped by the existing worker without mutation.

**Important:** normal Config-driven preparation still requires the complete family to be eligible. Mixed recovery is not a new automatic chat/subset-retry feature. Do not hand-edit the journal, reuse an old approval, or reset the fleet merely to clear a recovery state.

### Status evidence

Successful S3 step/reconciliation readbacks persist per-item `verified_at`. Summary reports the latest such saved event. The timestamp is not batch creation or file modification time, and it does not prove every resource is still compliant now. Old journals keep their counts and return no fabricated verification time.

The UI labels S3 as **saved batch readback** and SG as **current EC2 status read**. FAILED/DENIED and UNKNOWN batches remain visibly incomplete rather than displaying the consumed decision as if it were a completion result.

## How to reproduce offline

Use an isolated Python environment with Node.js available for integration syntax. From the repository root:

```sh
python -m pip install -r requirements-bulk.txt -r requirements-mcp.txt -r requirements-docs.txt
AWS_EC2_METADATA_DISABLED=true AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null bash scripts/check.sh
for file in integration/*.cjs; do node --check "$file"; done
mkdocs build --strict -f docs-config.yml
```

No AWS identity, runtime manifests, live endpoint, or credentials are required. The offline workflow runs the existing full suite on PRs/main with read-only repository permissions; documentation PR builds never deploy Pages.

Focused local validation used Python 3.13 and passed **47 tests** across `test_bulk`, `test_config_compliance`, `test_sg_compliance`, `test_phase17_19_support`, and `test_bulk_governed`. The local sandbox lacked the MCP package, so it is **not** the source of a full-suite PASS claim. Use the exact PR's GitHub Actions checks for the full dependency-installed suite and strict documentation build.

## Coverage and outstanding limits

Reviewed closely: the current Config reader, SG state machine, S3 state/status paths, operator adapters, exact-tool/governance boundaries, and associated regression tests. A credential-pattern scan covered all 166 tracked baseline source files and identified no matching credential literals. This is not a complete Git-history, issue/comment, screenshot, artifact, or credential-revocation audit.

Not certified by this work: live AWS interruption recovery, process/filesystem failure of every kind, hostile multi-user isolation, human identity binding inside Policy, host-wide least-privilege IAM, arbitrary subset remediation, full audit correlation, or production availability. Existing proof documents retain their original tested scope; a new green offline test does not rerun past AWS evidence.

See [Governance](../governance.md), [Demo v1](../demo-v1.md), and [Architecture](../architecture.md).
