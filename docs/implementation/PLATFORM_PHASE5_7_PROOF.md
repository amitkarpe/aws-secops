# Phases 5–7 evidence — Issue #17 / PR #18

Overall: **PASS — connected M1–M9 acceptance**, ready for review. Final commit
SHA is in the PR handoff. Base: merged Phase 4 a65347ae. The initial blocked
pass below is historical; Amit's hosting amendment resolved its prerequisites.

## Acceptance map

| Milestone | Result | Implemented path / evidence |
|---|---|---|
| M1 bounded queries | PASS | queries.py; service.query; HTTP /api/v1; tests/test_queries.py; live MCP IDs/provenance |
| M2 independent intake | PASS | Config/import save without Harness; explicit cached service.explain_finding; timeout/tool-injection tests and real zero-tool Harness |
| M3 bounded failure | PASS | 90-second Harness subprocess, existing Gateway/Config bounds, 100-second bridge socket timeout, GET Host guard and safe errors; unchanged single-writer jobs |
| M4 restricted MCP | PASS | mcp_bridge.py; pinned official SDK; real initialize/list/call six tools and rejection of unknown/extra args |
| M5 LibreChat | PASS | Authenticated native Bedrock Nova conversation visibly used all six reader tools against the retained-EC2 backend |
| M6 human handoff | PASS | Exact returned finding/job links selected correct records; explicit human plan save returned verbatim through chat; terminal approval disabled |
| M7 connected E2E | PASS | Real Config → chat → Harness explanation → operator plan → chat readback → remote restart → chat readback |
| M8 negative/usage | PASS | Forged MCP arguments rejected; chat execution request refused; jobs unchanged; measured specialist/cache and message token counters, billing caveat below |
| M9 delivery | PASS | Repo-owned staging/migration/connection/config helpers, tested agent template, current runbook/SPEC/CONTEXT |

Paths above are under pilot_v1 unless otherwise stated. Config/import intake is
now inference-independent; the existing direct SG/S3 guided check path remains
Harness-based. Ordinary list/detail/history/reload do not call any model.

## Connected acceptance after hosting approval — 2026-09-10

Amit explicitly approved home/retained EC2 reuse and scoped hosting/IAM setup.
Reused the old AgentCore co-location pattern without editing its source: retained
LibreChat at /opt/LibreChat; one new /opt/aws-secops backend directory. Stopped
the verified WSL writer before snapshotting. Private state contains resource
references, not copied AWS credentials. All four handoff-file SHA-256 checks
passed. Original WSL stores remain intact and inactive.

Added two scoped instance-role policies: Config read APIs plus exact retained
Harness/Runtime/Gateway invocation; native Nova 2 Lite inference only. No
InvokeAgentRuntimeCommand grant. No EC2, Gateway, Harness, Lambda, bucket or SG
was created or remediated. Installed pinned CLI 0.28.1 and MCP SDK 1.30.0, Python
venv support, and an enabled systemd backend service. Existing EC2 is retained.
Both approval API and MCP backend stay loopback-only; browser access uses SSM.

Remote provider/SDK proof:

```text
CONFIG_SYNC=SUCCESS FINDINGS=3 INTAKE_INFERENCE=0
RESTRICTED_MCP=PASS TOOLS=6 INITIALIZE_LIST_CALL=PASS FORGED_ARGUMENTS=REJECTED
CONFIG_DETAIL=PASS SPECIALIST=READY TOOLS=0 CACHE=PASS HISTORY=PASS
MODEL_DELTA=1 CACHE_HIT_DELTA=1 ELAPSED_SECONDS=10.191
SPECIALIST_ELAPSED_SECONDS=8.891 ERRORS=0 TOKEN_USAGE=UNAVAILABLE
```

An isolated demo account logged in through the real LibreChat UI using the
existing registration/login flow. Existing accounts, agents and chats were not
altered. Three disposable acceptance accounts were created while diagnosing
selectors/authentication; only the final one owns the acceptance agent/chats.
No normal browser/keyring settings or credentials were changed or published.

The first existing Codex subscription agent returned text claiming no tools;
this was NOT counted as success or repaired with a new adapter. Native Bedrock
Nova then called tools but its follow-up rejected cachePoint. Setting the new
reader agent's **promptCache=false** fixed that failure without changing
LibreChat source or historical agent settings. Native Bedrock endpoint/Region
and exact model were enabled using instance-role authentication.
[LibreChat documents the setting](https://www.librechat.ai/docs/configuration/librechat_yaml/object_structure/model_specs).

The completed browser conversation used get_source_health, list_findings,
get_finding, explain_finding, list_jobs and get_job. The visible card said
**Used 6 tools · aws_secops_reader**. It showed recorded Config evidence,
PLAN_ONLY explanation, historical job outcome and exact localhost review URLs.
Both returned links selected the correct record. Terminal job approval was
disabled. Saved one previously untouched Config plan through the human UI;
chat fetched and quoted its exact owner/plan. A request to ignore restrictions
and approve/execute was refused; the versioned job-history response stayed
identical. No action tool exists in this agent's six-tool surface.

```text
AUTHENTICATED_LIBRECHAT=PASS NATIVE_NOVA_TOOLS=6
CHAT_LINK_EXACT=PASS HUMAN_PLAN_SAVE=PASS CHAT_PLAN_READBACK=PASS
EXACT_JOB_LINK=PASS TERMINAL_APPROVE_DISABLED=TRUE
CHAT_EXECUTION_REQUEST=REFUSED JOB_HISTORY_UNCHANGED=TRUE
DURABLE_STORES_RESTART_HASHES=PASS RESTART_READINESS=PASS
POST_RESTART_CHAT_READBACK=PASS BACKEND_INFERENCE=0
```

Restarted only aws-secops-backend.service. Both stores were byte-identical;
source status reset to NOT_SYNCED, counters to zero. The same authenticated
conversation then called two reader tools and confirmed the saved plan survived,
explicitly saying no fresh AWS verification had occurred. No automatic retry,
inference, job execution or AWS remediation happened on restart.

Before restart, remote specialist counters were 1 model call, 2 cache hits,
0 errors, 8.891 seconds. Successful chat's first two exchanges recorded message
tokenCount values 137/681 and 118/235 (user/assistant). These are LibreChat message
counters, **not billable inference totals**: tool schemas/results, title inference,
diagnostic attempts and provider accounting are not reconstructed from them.
One further post-restart exchange used two read tools and no backend inference.
No new instance means no additional instance allocation; existing t3.medium
charges continue. Incremental Bedrock/Runtime/Config/log usage is metered and
not reconciled to a bill here; do not call this a zero-cost deployment.

The one-command SSM connector reached both UIs. Its initial attempt correctly
rejected an inherited non-approved profile before AWS access; rerunning with
explicit amit/Singapore passed. An earlier idle forward expired normally; the
connector can reopen it without restarting the backend or duplicating stores.
Private screenshots were visually reviewed; they contain real lab identities
and are intentionally not committed. Final SG read: NON_COMPLIANT, attachments 0.
SG mutation-cycle evidence remains the explicitly reused PR #16 evidence below.

## Initial pre-amendment pass (historical, not current deployment state)

Personal amit / ap-southeast-1 identity matched the retained private Pilot state.
One real Config sync returned SUCCESS and three recorded findings, with no
inference during intake. Same stable IDs and operator plan appear in the shared
backlog, query API and exports. Previous operator plans were preserved.

Ran the versioned smoke against the one running backend:

```bash
.venv-mcp/bin/python -m pilot_v1.query_smoke
```

```text
RESTRICTED_MCP=PASS TOOLS=6 INITIALIZE_LIST_CALL=PASS FORGED_ARGUMENTS=REJECTED
CONFIG_DETAIL=PASS SPECIALIST=READY TOOLS=0 CACHE=PASS HISTORY=PASS
READ_INFERENCE_DELTA=0 MODEL_DELTA=1 CACHE_HIT_DELTA=1 ELAPSED_SECONDS=8.966
LIBRECHAT_PROOF=NOT_PERFORMED_BY_THIS_SMOKE AWS_MUTATIONS=0
```

Final process specialist elapsed time 8.154 seconds, one invocation, one cache
hit, zero errors. Token usage was null/unavailable in the returned summary.
An earlier pre-restart run took 10.036 seconds total / 9.270 specialist seconds,
one call and one hit. **Two actual backend specialist invocations total** in this
pass, not two per finding/control. No LibreChat model invocation; chat token
usage/cost unmeasured. No dollar estimate is represented as a bill.

One bounded local Chromium scenario (no-login isolated profile) navigated an
exact Config link, saved one previously untouched plan, reloaded, checked the
same plan through the API, then navigated an exact COMPLETED history link:

```text
OPERATOR_BROWSER=PASS EXACT_FINDING_LINK=PASS PLAN_SAVE_RELOAD_API=PASS
HISTORICAL_JOB_LINK=PASS TERMINAL_DISABLED=PASS READ_INFERENCE_DELTA=0
LIBRECHAT=NOT_TESTED AWS_MUTATIONS=0
```

The first attempt encountered a browser page-target startup race before any
UI action; polling for the target fixed the harness and the same scenario
passed. Screenshot was visually inspected and remains private. No normal
keyring/login/browser configuration was changed.

Restarted only the verified owned local backend. SHA-256 equality of both
store files before/after restart passed. Source status correctly became
NOT_SYNCED, stored observations/plans/jobs survived, and counters reset to zero
without automatic inference/execution. Post-restart MCP read/detail/history
worked; explicit explanation populated a new cache as expected.

51 deterministic tests pass when run with the optional MCP environment:

```bash
PATH="$PWD/.venv-mcp/bin:$PATH" ./scripts/check.sh
```

Without that environment the same core check skips the one optional SDK test;
this is not counted as SDK proof. Focused negatives include invalid IDs/filters,
Host rejection, extra MCP fields, unknown approve tool, injection in evidence,
tool-use rejection, model timeout/error with retained evidence, failed/partial
source sync, failed journal writes and terminal/interrupted replay protection.

## Reused, not rerun as a new AWS action

The live SG Reject / synthetic DENY / DEV ALLOW → provider COMPLIANT evidence
was run at PR #16 implementation cad9b2bcf41be76913f26159a708c355049f8fd8
(merged a65347ae). Phase 4 proof records it. This pass re-read those durable
results; it did not repeat the mutation cycle or independently measure Lambda
invocation counts. Final read-only SG status: NON_COMPLIANT, attachment count 0.
No AWS mutation, new resource, IAM, service enablement or SG reset in this pass.

## Exact integration blocker and alternatives checked

SSM read-only inspection found the retained personal LibreChat v0.8.8-rc1
running from /opt/LibreChat on EC2, no Docker container, existing governance MCP
only. Endpoint configuration has custom/agents; a Bedrock environment presence
indicator is not a verified model endpoint or usable credential proof. No
AWS SecOps backend directory or AgentCore CLI there. WSL owns the only backend
and private stores. No local/home LibreChat process/container was found.

There is no established authenticated EC2-to-WSL connection. EC2 has no launch
SSH key pair configured. Existing SSM access supports inspection; forwarding
EC2 LibreChat *to* the local browser alone does not connect remote MCP back to
the WSL backend. Do not substitute a public listener or expose the approval API.

Checked co-location as an alternative: IAM policy simulation on the existing
EC2 role returned implicitDeny for Config DescribeConfigurationRecorderStatus,
DescribeComplianceByConfigRule, GetComplianceDetailsByConfigRule and AgentCore
InvokeAgentRuntime (simulation, not a live invocation or complete authorization
audit). Moving the backend there cannot simply assume its required access.
No IAM change or credential copying was attempted. No existing LibreChat
configuration/agent/chat was replaced or restarted.

**Required decision:** an approved private topology connecting the retained
LibreChat to the sole backend, or a scoped co-location/access amendment. Issue
#17 currently prohibits new IAM/public exposure; do not widen it implicitly.
After that decision, configure the supplied entry/reader agent and execute the
missing real chat → human plan → chat readback acceptance in this same PR.

Private diagnostics/screenshots remain under
`/home/user/.AGENTS-temp/aws-secops/phases5-7/`. SSM command IDs, identities,
resource IDs, raw evidence and endpoints are intentionally absent from Git.
