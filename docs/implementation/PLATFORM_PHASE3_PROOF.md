# Phase 3 — durable compliance backlog

Authority: Issue #13 / PR #14. Status: M1–M5 PASS, ready for review.

## Implementation

- Stable SHA-256 finding ID from the normalized source, resource type, resource
  ID and control. Human/AI prose does not define identity.
- `first_seen` and `last_seen` are server ingestion times, distinct from
  provider `observed_at` and `synced_at`. `occurrence_count` counts batches in
  which the item appeared, not unique AWS events; duplicates within one batch
  count once.
- A successful bounded Config sync marks previously stored Config provider
  items absent from that response `seen_in_latest_sync=false`. It does not
  change their compliance status, last-seen time or plan. Partial snapshots can
  omit still-noncompliant resources. Failed sync leaves stored work untouched.
- One versioned JSON file, maximum 100 findings/1 MB, atomic same-directory
  replacement after flush/fsync, mode 600. Validation/write failure does not
  replace in-memory or prior disk state. Invalid store stops startup.
- Operator-only owner, mitigation plan, target/timeline and UNPLANNED/PLANNED
  metadata. Imports cannot overwrite plans or submit tracking fields. The
  `/api/plan` action accepts exactly those fields and an existing finding ID,
  through same-origin JSON with bounded strings. It performs no model/AWS call.
- The same open records feed UI and CSV/Markdown exports. Provider status and
  PLAN_ONLY remain independent of the plan. The existing SG execution path is
  unchanged; a saved plan is not an approval.

## Amit's browser check

No agent reconfiguration or LibreChat login is required. This is the existing
AWS SecOps thin UI, **not** the older AgentCore LibreChat demo.

1. Open `http://localhost:3340/`.
2. Click **Sync AWS Config**. Expected: recorded provider findings, PLAN_ONLY,
   and source health SUCCESS or explicitly PARTIAL. No AWS mutation.
3. Under **Operator mitigation plan**, choose an open finding. Enter owner,
   a single-line mitigation plan and target; select PLANNED and click
   **Save local plan**. Expected: `SAVED — local plan persisted`, planned count
   increases and compliance stays unchanged.
4. Reload. The same finding ID and plan remain. Restart the application with
   the same server-side store setting; the plan still remains. Source-health
   status resets to NOT_SYNCED for the new process; this does not erase stored
   evidence or claim a fresh provider sync.
5. Sync again. Expected: same ID/plan, updated last-seen and count if returned.
   Missing records remain open and say NOT SEEN, not COMPLIANT.
6. Download CSV or Markdown. Expected: the same stable ID, tracking and plan.

## Operations and reproducible validation

From the repository, start the existing loopback application:

```bash
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 ./scripts/pilot-v1.sh serve
```

Default private store: `~/.local/state/aws-secops/backlog.json`. The server-side
`PILOT_BACKLOG_FILE` environment variable can select a different private file;
the browser/model cannot. Do not run two app processes against the same file.
Git ignores accidental local backlog copies, but never stage raw private data.

Run the following with no other writer on that store:

```bash
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 ./scripts/pilot-v1.sh durable-smoke
```

It owns
two sequential child servers on OS-selected loopback ports, does two real
Config/Harness syncs, creates one local demo plan on a blank unplanned Config
item, restarts, and verifies ID/plan/tracking/exports and PLAN_ONLY rejection.
It preserves the store and will stop if there is no blank unplanned Config
item, rather than overwrite an operator plan. To repeat independently, select
a new private `PILOT_BACKLOG_FILE` in the command environment.

Do not use the older full `smoke` for Phase 3 validation: that command includes
the separately scoped SG rearm/remediation cycle. No AWS resource cleanup is
needed for this phase. Local stores are retained; back them up before any
manual recovery. Automatic pruning, multi-writer access and schema migration
are intentionally not included. At 100 identities, new records fail without
evicting prior plans.

## Evidence

Live API/restart proof (personal amit, Singapore; identity matched the private
retained Pilot configuration before invoking anything):

```text
PLATFORM_PHASE3_DURABLE_SMOKE=PASS
SOURCE=AWS_CONFIG COUNT=3 RESTART=PASS PLAN_RETAINED=PASS TRACKING=PASS EXPORT=PASS TOOLS=0 AWS_MUTATIONS=0
```

Two Config syncs and two retained Nova/Harness explanations; zero effective
tools in those explanations. Approval attempts on this PLAN_ONLY workflow
returned HTTP 400. The test retained one local plan, same ID and first-seen,
updated last-seen, and exactly one additional sighting after restart/resync.

One real local Chromium smoke, using the existing cached browser and its
DevTools protocol (no added framework), clicked Save local plan, checked the
SAVED result, reloaded, and confirmed the persisted form/backlog. No further
AWS/model call was needed for this browser test:

```text
PLATFORM_PHASE3_BROWSER=PASS SAVE_CLICK=PASS RELOAD=PASS CONSOLE_ERRORS=0
count=3 planned=1 planRetained=true eligibility=PLAN_ONLY
```

Screenshot visually inspected. Private browser script/screenshot are retained
under `/home/user/.AGENTS-temp/aws-secops/platform-phase3/`; do not publish raw
identities or screenshots. The refreshed app at localhost:3340 loaded the
same three records and one plan from the durable store.

40 deterministic tests pass, including focused stable-ID, reconciliation,
restart, corrupt-store, failed-write/sync, bounded planning/API and PLAN_ONLY
guards. Existing SG tests remain unchanged. No live SG write was run.

No AWS resources, IAM or service configuration were created or modified.
Existing Config reads and two Harness/model explanations are the only AWS
usage; no new recurring infrastructure or cleanup obligation was introduced.
Costs were not independently metered in this phase. Scope deviations: none.
