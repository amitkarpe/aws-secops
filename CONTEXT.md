# Context

Status: Phases 5–7 / Issue #17 / PR #18 — BLOCKED_INTEGRATION; backend/MCP proved

## Current Truth

- Phase 4 merged as a65347ae. Active work is the nine-milestone restricted
  LibreChat integration in PLATFORM_PHASE5_7_PLAN.md. Chat is read/explain only;
  the existing single-writer human UI retains all planning and approval writes.
- M1–M4 implemented and validated, local exact-link/plan/restart proof passed.
  Actual LibreChat conversation is not proved: retained v0.8.8-rc1 runs on EC2,
  backend/store on WSL; no established private reverse path. Co-location would
  also need permissions absent from the existing EC2 role (simulation evidence).
  No remote LibreChat, IAM, AWS resource, credential or network configuration changed.

- Phase 3 merged via PR #14. Current work connects the direct supported SG
  finding to durable jobs, exact preview, single-use decisions and restart-safe
  history. No new AWS resources, actions or IAM permissions.
- Phase 4 live proof passed Reject/no call, synthetic Policy DENY, DEV ALLOW
  with independent provider COMPLIANT, terminal replay rejection and actual
  restart history retention. The dedicated demo SG was restored NON_COMPLIANT
  and unattached. Browser history/reload/disabled terminal approval passed.

- Phase 2 merged as PR #12. Phase 3 adds server-owned stable IDs, atomic local
  JSON persistence, sighting tracking and a narrow operator planning action.
- Config records missing from later bounded snapshots remain unresolved with
  seen_in_latest_sync=false. Plans survive sync/import independently of provider
  compliance. No AWS mutation capability was added or exercised in this phase.
- The application defaults to ~/.local/state/aws-secops/backlog.json. Private
  backlog data must never be committed. A corrupt store stops startup.
- Live proof passed: three real Config records, plan saved, actual process
  restart, same ID/plan restored, repeated sync reconciled, CSV/Markdown matched.
  One Chromium smoke clicked Save local plan and reloaded successfully. Zero
  specialist tool calls and zero AWS mutations; no new browser framework.

- Phase 1 merged through PR #10. PR #12 implements Phase 2 using existing AWS
  Config in the personal Singapore lab: read-only bounded sync, specialist
  explanation, provenance/freshness, and export. Three live evaluations passed
  the API smoke with zero tool calls and PLAN_ONLY approval rejection.
- Config sync reports SUCCESS/PARTIAL/ERROR and retains its previous snapshot
  on error. Evaluation and sync times are separate. No AWS resources, IAM or
  service configuration changed. The following bullets record the retained base.
- The retained Pilot v1 Harness, Gateway, Policy, exact SG remediation, S3
  read, and loopback UI remain the proven base.
- Live work uses only the approved personal `amit` profile in Singapore.
- Private resource identities and raw evidence remain outside this public repo.
- M1 added one repo-owned live smoke command and proved SG finding, Reject
  no-change, synthetic Policy DENY no-change, DEV ALLOW with provider
  COMPLIANT, read-only S3, and final SG reset to NON_COMPLIANT.
- M2 added one common SG/S3 finding contract plus bounded deterministic JSON
  and CSV import with public-safe samples; no new live source integration.
- M3 added a deterministic provider-backed management backlog to the existing
  single-user API/UI with totals, grouping, priority/age, and recommended focus.
- M4 expanded the exact S3 read tool to two server-owned buckets, proved 10
  provider controls (9 PASS / 1 safe versioning exception), and made zero S3
  mutations; the caller/model cannot select buckets.
- M5 added CSV and Markdown reduction-plan exports from the same bounded open
  findings used by the UI; no second reporting store or AWS write was added.
- The Pilot v1.1 baseline previously passed 26 deterministic tests, one live end-to-end API
  smoke, provider readback, public-safety review, and one headless browser
  smoke of the management screen.
- Platform Phase 1 adds same-origin bounded content upload through the existing
  loopback API/UI. The browser supplies file content plus a basename, never a
  filesystem path.
- Public-safe CloudSCAPE-style compliance and VAPT-style vulnerability fixtures
  map through two explicit adapters into the existing common contract.
- Specialist routing and action eligibility are deterministic and server-owned:
  CloudSCAPE/AWS compliance routes to `Compliance Agent`, VAPT routes to
  `Vulnerability Agent`, and all imported evidence is `PLAN_ONLY`.
- The only `REMEDIATION_SUPPORTED` record remains the provider-backed exact
  public-SSH Security Group finding; Reject, synthetic Policy DENY, DEV ALLOW,
  exact Lambda, and provider re-read behavior remain unchanged.
- Final Platform Phase 1 acceptance passed 29 deterministic tests, one live
  import/routing/plan-only/SG/S3/export API-provider smoke, and one headless
  browser-visible operations-screen smoke.

## Next Action

- ChatGPT resolve the private deployment/connectivity gate in the same PR #18;
  then complete the real chat segment and measurements. Do not mark Ready/merge
  or treat the standalone MCP/local browser proof as complete integration.
