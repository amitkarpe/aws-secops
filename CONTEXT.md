# Context

Status: Phases 5–7 / Issue #17 / PR #18 — connected acceptance PASS; ready for review

## Current Truth

- Approved named UI extension is deployed on the retained EC2: one Nginx,
  HTTPS chat plus separately authenticated operator entry, and unchanged legacy
  DNS/HTTP route. Both application backends remain loopback-only. Public access
  remains limited to the existing trusted source IP. Browser chat-to-exact-review
  and origin/auth boundaries passed; see NAMED_UI_DEPLOYMENT.md. No workload
  remediation occurred. Private credentials/evidence stay outside Git.

- Amit's 2026-09-10 amendment authorizes home/retained EC2 reuse and scoped
  hosting/IAM/private connectivity prerequisites. SPEC records the approval;
  reuse the old EC2 co-location pattern while preserving read-only chat tools.

- Phase 4 merged as a65347ae. Active work is the nine-milestone restricted
  LibreChat integration in PLATFORM_PHASE5_7_PLAN.md. Chat is read/explain only;
  the existing single-writer human UI retains all planning and approval writes.
- M1–M9 implemented and validated. Sole backend/stores now live beside LibreChat
  at /opt/aws-secops on the retained EC2. Original WSL files are retained but
  their writer is stopped: do not start the old local serve command.
- Native Bedrock Nova chat used all six reader tools. Explicit promptCache=false
  avoids the installed provider's cachePoint follow-up error. The old Codex
  subscription path returned text without tools and was not accepted as proof.
- Real chat -> exact operator link -> saved human plan -> chat readback/refusal
  passed. Remote restart preserved both stores byte-for-byte; source freshness
  resets honestly. Scoped role policies, native Bedrock config and an additive
  read-only MCP entry were installed under Amit's amendment. No new EC2 or
  resource remediation occurred. Historical agents/chats remain intact.
- Use scripts/connect-retained-ui.sh with the private retained Name tag and
  explicit AWS_PROFILE=amit / AWS_REGION=ap-southeast-1. Operator localhost:3340;
  LibreChat localhost:13080. The runbook has the tested reader settings.

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

- ChatGPT review the final connected M1–M9 evidence and full PR #18 diff, then
  merge if clean. No next scope is invented here. Preserve the retained backend
  and its sole store; Amit can create his reader using the tested agent template.
