# Phases 5–7 evidence — Issue #17 / PR #18

Overall: **BLOCKED_INTEGRATION**, not a complete release PASS. Final commit SHA
is in the single PR handoff (avoids a self-referential commit hash). No Ready or
merge action. Base: merged Phase 4 a65347ae.

## Acceptance map

| Milestone | Result | Implemented path / evidence |
|---|---|---|
| M1 bounded queries | PASS | queries.py; service.query; HTTP /api/v1; tests/test_queries.py; live MCP IDs/provenance |
| M2 independent intake | PASS | Config/import save without Harness; explicit cached service.explain_finding; timeout/tool-injection tests and real zero-tool Harness |
| M3 bounded failure | PASS | 90-second Harness subprocess, existing Gateway/Config bounds, 100-second bridge socket timeout, GET Host guard and safe errors; unchanged single-writer jobs |
| M4 restricted MCP | PASS | mcp_bridge.py; pinned official SDK; real initialize/list/call six tools and rejection of unknown/extra args |
| M5 LibreChat | BLOCKED | EC2 runtime inspected; no private connection from existing deployment to WSL backend; nothing installed remotely |
| M6 human handoff | PARTIAL | Exact finding/job links and local browser plan save/reload/API pass; chat leg not performed |
| M7 connected E2E | BLOCKED | Config → MCP → Harness and operator UI/history/restart pass; no LibreChat conversation proof |
| M8 negative/usage | PARTIAL | Focused tests, actual MCP negatives and measured specialist/cache/latency; chat metrics unavailable |
| M9 delivery | PARTIAL | One runbook/config template and this proof; connected release not accepted |

Paths above are under pilot_v1 unless otherwise stated. Config/import intake is
now inference-independent; the existing direct SG/S3 guided check path remains
Harness-based. Ordinary list/detail/history/reload do not call any model.

## Freshly executed evidence

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
