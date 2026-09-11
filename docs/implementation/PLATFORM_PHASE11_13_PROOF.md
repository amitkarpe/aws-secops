# Phases 11–13 implementation and acceptance

Authority: Issue #22 / PR #23. Status: **M1–M9 PASS, ready for review**.
Fresh evidence: 2026-09-11. No 1,000-live claim; no self-merge.

## Architecture decision

Selected **Gateway → Policy → Lambda → exact S3 BPA API**, in vagent/Singapore.
The architecture review was posted before deployment in PR #23. AWS target
documentation does not list SSM Automation/Document as a first-class target.
SSM would add a wrapper, automation role and execution state for this one API.
It is more useful later for an existing multi-step operational runbook.
Smithy target support is RestJson rather than S3's RestXml protocol; no direct
Smithy shortcut is claimed. No existing bounded vagent API target was available.

Sources: [Gateway targets](https://docs.aws.amazon.com/help-panel/bedrock-agentcore/latest/console/hp-gateway-targets.html),
[Smithy targets](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-building-smithy-targets.html).

## Fresh evidence

| Acceptance | Evidence | Result |
| --- | --- | --- |
| Exact execution intent | One separate MCP tool; only batch_id and approval_hash; current immutable server scope | PASS |
| Native ASK Reject | Real authenticated LibreChat, Reject + Submit; PENDING 5 unchanged, Gateway calls 0 | PASS |
| Native ASK Approve | Fresh card, Approve + Submit; exact five-bucket worker run | PASS |
| Provider verification in same chat | Same conversation readback: verified 5/5, all four BPA flags true | PASS |
| Gateway Policy DENY | Synthetic prod request, explicit -32002 policy denial; Lambda START events 0 | PASS |
| Gateway Policy ALLOW | Same exact tool/dev, already-compliant bucket; Lambda START event 1; no S3 change | PASS |
| Browser-independent execution | Browser evidence polling lost connectivity after approval; remote worker completed five, no approval retry | PASS |
| Completed restart | Real service restart preserved five-bucket journal SHA-256 byte-for-byte | PASS |
| In-flight recovery | Ten-bucket API proof: SIGKILL → UNKNOWN → read-only reconcile → explicit continuation → fresh preview/approval | PASS |
| Ten-bucket verification | 10/10; final preview COMPLETED 3 + SKIPPED 7; elapsed 39.44s; zero provider errors | PASS |
| Fifty-bucket gate | Quota 10,000, used 13 before growth; FREE/ACTIVE plan; 50 owned empty reset/readback | PASS |
| Fifty-bucket execution | 50 COMPLETED / 50 Gateway calls / 50 target successes; 70.353s; API/provider proof | PASS |
| Hundred-bucket gate | Quota 10,000, used 53 before growth; FREE/ACTIVE; 100 owned empty buckets reset/read back | PASS |
| Hundred-bucket native acceptance | Authenticated same-chat finding → ASK Reject → fresh ASK Approve → 100 COMPLETED → visible 100/100 readback; no Operator page visits | PASS |
| Hundred-bucket counts | Rejected: PENDING 100, Gateway 0. Approved: Gateway 100, target success 100, provider errors 0; browser page errors 0 | PASS |
| Final-scope Policy probe | DENY Lambda START count 0; ALLOW count 1, ALREADY_COMPLIANT; no S3 mutation | PASS |
| Final completed restart | Actual service restart preserved the 100-item completed journal hash | PASS |
| Repeat-demo reset | One-command guarded reset/readback of 100; fresh PENDING 100; all three services active | PASS |

The native browser automation encountered transient network unreachability
after successful approval. It did not repeat the mutation. EC2 journal readback
and a read-only prompt in the **same conversation** established final success.
No Operator webpage was required. The final 100-bucket browser run completed
without that network failure; screenshots were visually inspected in light
mode. API recovery proof is not labeled browser
proof. Process metrics are cumulative, not a billing meter; interruption loses
unsaved process counters, so they are not claimed as an exact lifetime total.

The isolated SDK client reuses connections for fleet reads, checks expected
bucket owner, retries only explicit read throttling, and disables SDK write
retries. Live direct-write fallback was removed. Lambda performs its own exact
ownership/precondition check; completion requires a separate worker S3 read.

## Policy probe boundaries

Fresh private evidence window in epoch milliseconds:
start 1789101548797; denied-window end 1789101555854; end 1789101570575.
Bounded CloudWatch Lambda START records: DENY 0, ALLOW 1. The ALLOW probe
returned ALREADY_COMPLIANT, so neither probe mutated S3. The exact Gateway
must be READY, AWS_IAM and ENFORCE; the expected active policy definition and
single-policy inventory are checked before execution. Generic failures never
count as Policy DENY. The model may refuse other requests before tool dispatch;
that is not independent Gateway evidence.

## Retention and cost

Final-scope probe window: start 1789106780156; denied-window end 1789106781184;
end 1789106783091. Repo-owned `probe-bulk-policy.py --verify-logs` independently
read the bounded Lambda START counts (0/1). All probe provider reads succeeded.

Reused retained EC2, existing hosting, original SG path and supplied profiles.
New vagent resources: one Gateway/target, one Policy engine/policy, one 128-MB
Lambda, one log group (seven-day retention), two scoped roles and the bounded
empty demo fleet (**100 retained buckets**). TTL review: **18-09-26**. No extra EC2, scanner or account-level
protection changes. Resources remain for repeat demos; cleanup is not claimed.

At published rates, 100 tool requests cost approximately $0.0005 Gateway plus
$0.0025 Policy = **$0.003**, excluding Lambda duration, S3 API, logs and chat
inference. This is a formula, not measured billing or a claim of free credits.
No model runs per bucket. SDK/API counters exclude Lambda-internal requests.
Hosting is the existing retained instance, not zero-cost infrastructure.
Source: [AgentCore pricing](https://aws.amazon.com/bedrock/agentcore/pricing/).

## Proof privacy and operator handoff

Raw screenshots, conversation IDs, resource names, manifests, AWS responses and
identity hashes stay private. The user-facing guide is
`docs/operations/LIBRECHAT_BULK_DEMO.md`. Original WSL manifest is retired;
the authoritative bulk journal and worker now live on EC2. Do not start a second
writer from the old WSL files. Native per-tool ASK remains the human boundary;
the supplied broad lab profile is not represented as an IAM-isolated worker.

Final deterministic check: `PATH="$PWD/.venv-mcp/bin:$PATH" ./scripts/check.sh`
passed **69 tests, no skips**; offline 1,000-item run 88.801s in that run.
Focused exact executor, Lambda scope, async replay, explicit DENY versus UNKNOWN
and SDK no-write-retry checks passed. Shell/Node/Python syntax and diff checks
passed. Private meeting HTML passed desktop/mobile image, overflow, anchor,
theme and no-network checks. The stock HTML scanner flagged embedded PNG bytes
and the explicit navigation link; visible-text/DOM/network checks ruled out
those false positives. Raw evidence is deliberately not committed.

Initial delivery retained state: **100 NON_COMPLIANT, PENDING**, prepared for Amit's next
native approval demo. The successful completed journal is archived, not erased.
Reset did not alter objects, bucket policies, ACL ownership or account-level BPA.
Final HEAD is recorded in the PR handoff rather than self-referenced here.

## Approval-copy follow-up — 2026-09-11

Amit reported successful completion of all five prompts, but shared a confusing
S3 approval card with the old SSH-removal description. Live configuration
confirmed that `endpoints.agents.toolApproval.reason` was endpoint-wide and
still described the SG demo. The installer now replaces that recognized legacy
copy with resource-neutral text, preserving ASK/ALLOW/DENY matchers and hooks.
It refuses an unrecognized custom reason rather than overwriting it silently.
The S3 agent separately describes only its own action; SG tools are unchanged.

S3 instructions now explicitly stop after read-only requests, require a fresh
explicit fix request for execution intent, distinguish blocked/cancelled tools
from an evidenced Gateway DENY, and prohibit speculative verified results or
policy-exception advice. These are model instructions, not a replacement for
native approval or Gateway authorization.

Fresh authenticated browser check using Amit's exact prompt, "Read only the
selected demo buckets. No changes.": two reader tools, no executor call, no
approval card, no SG wording, unchanged summary, zero browser errors. The
existing journal reported **100 COMPLETED / verified 100**. This was preserved;
no reset, remediation, IAM or Gateway policy change was performed. A new pending
ASK card was not exercised because that would require resetting the completed
fleet; live configuration readback plus the focused installer regression test
cover the shared-copy correction. Previous 100-bucket ASK/Approve proof remains
the execution evidence, supplemented by Amit's own successful run report.

Final follow-up check: **70 tests PASS, no skips**, plus diff/syntax checks.
Only LibreChat was restarted to load configuration; the batch journal hash was
unchanged and all three services remained active. Start a new chat to use the
updated S3 instructions; historical messages/cards are not rewritten.
