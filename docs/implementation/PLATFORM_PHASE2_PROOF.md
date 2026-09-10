# Platform Phase 2 proof

Date: 2026-09-10 (Singapore). Authority: Issue #11 / PR #12.

## M1 — Source selection: PASS

The `amit` caller matched the private retained Pilot account before live reads;
Region was explicitly `ap-southeast-1`. Config's existing recorder returned
`recording=true`, `lastStatus=SUCCESS`. Two rules returned usable noncompliant
evaluations. Config was the first usable candidate; Inspector and Security Hub
were not needed or enabled. No AWS configuration changed.

## M2–M4 — Adapter, sync and provenance: PASS

`POST /api/sync-provider` accepts only an empty JSON object. Profile, Region,
source and read operations are server-owned. Reads cover recorder status,
noncompliant rule summaries and evaluations, capped at ten rules / 100 records.
No pagination is followed; a continuation token or omitted rules marks PARTIAL.

The adapter maps Config resource/rule identity, status, annotation, and
`ResultRecordedTime`. INFO means unspecified severity because Config provides
no severity rating. Long resource identities are hashed to fit the common
contract. Runtime identities remain private and are not committed.

Config records route to Compliance Agent through the retained Nova 2 Lite /
Harness, with no effective tools. All Config results, including SG evaluations,
are PLAN_ONLY; the direct SG workflow remains the only supported action path.

The UI and exports distinguish AWS_PROVIDER from IMPORTED, observation from
sync time, and SUCCESS/PARTIAL/ERROR. Failed sync preserves the last snapshot
and last-success time; successful sync replaces only Config entries. Missing
entries are absent from the snapshot, never asserted COMPLIANT.

## M5 — Live acceptance: PASS

With the repo app running at `http://localhost:3340/`:

```bash
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 ./scripts/pilot-v1.sh provider-smoke
```

One live API smoke returned:

```text
PLATFORM_PHASE2_PROVIDER_SMOKE=PASS
SOURCE=AWS_CONFIG STATUS=SUCCESS COUNT=3 TOOLS=0 ELIGIBILITY=PLAN_ONLY
```

The snapshot comprised two Security Group and one S3 evaluation. Compliance
Agent explained the recorded SSH/S3 control findings from their evidence.
Approval returned HTTP 400 before Gateway/remediation; both exports contained
the same source records, provenance, and observation/sync times.

One headless Chromium render of the populated app confirmed SOURCE_SYNCED,
SUCCESS with three findings, AWS_PROVIDER, Compliance Agent and PLAN_ONLY.
Browser proof covered rendering; the API smoke exercised sync. Private
screenshot/DOM evidence lives under
`/home/user/.AGENTS-temp/aws-secops/platform-phase2/` and must not be published.

35 deterministic tests pass. Tests cover mapping/time validity, bounds/PARTIAL, server-owned parameters,
specialist routing, PLAN_ONLY rejection, snapshot replacement, empty results,
and error retention. Full deterministic checks and diff/public-safety review
passed before publication.

## Retention and limits

No AWS resource, IAM, service configuration or infrastructure mutation occurred;
no cleanup is needed. One specialist inference used retained Harness/model
capacity. No new recurring infrastructure was introduced. Source health and
backlog are in memory and reset with the app. Sync is manual and bounded, not
an account-wide completeness claim. Evaluation freshness depends on the
existing Config schedule; a recent fetch does not make old evidence current.

Official references:

- [Config compliance summary](https://docs.aws.amazon.com/cli/latest/reference/configservice/describe-compliance-by-config-rule.html)
- [Config evaluations and timestamps](https://docs.aws.amazon.com/cli/latest/reference/configservice/get-compliance-details-by-config-rule.html)
