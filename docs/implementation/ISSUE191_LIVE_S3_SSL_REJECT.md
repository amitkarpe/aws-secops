# Issue #191: live `s3_ssl` Reject-only evidence

This packet records the bounded, public-safe portion of Issue #191. It is not
an acceptance claim for the authenticated LibreChat native-card journey.

## Fixed live collector

`scripts/issue191_live_s3_ssl_reject.py` accepts no account, bucket, role, or
operation input. It uses the personal-LAB `amit` profile only, resolves exactly
`lab-dev`, `lab-poc`, `lab-qa`, and `lab-sec` from Organizations, verifies the
assumed identity for each existing read role, and issues only S3 `ListBuckets`
and `GetBucketPolicy` reads. The selected region is `ap-southeast-1`.

The collector limits each account to 20 buckets, emits aliases and hashed
resource references only, and makes no AWS write or executor call. An account
or alias mismatch fails closed. Provider errors remain `UNAVAILABLE`; an absent
bucket policy is a `NON_COMPLIANT` result for this TLS control.

## Sanitized live run

The repo-owned runner completed with all four expected aliases identity-verified
and `AVAILABLE`. It collected once, froze one `lab-dev` `s3_ssl` candidate,
made a local bounded `REJECT` decision, then collected again. The canonical
provider evidence digest was unchanged:

| Evidence | SHA-256 digest |
| --- | --- |
| provider evidence before and after Reject | `db9d3cd8fba4e52a96fc8b8eedc765d1cd9c5a35646b8fa1e38bee4456ce9808` |
| frozen batch | `df1eaa48a78e8b5804200625f1d6bc5a695c963631f1ecb459a364d55d9d84c7` |
| frozen scope | `c004be7e2a2b2b160847cf3feb4646855011a472fb7aa87a97f6f62129ef6998` |

The local decision result was `REJECTED`, with `remediation_dispatches = 0`,
`aws_writes = 0`, `automated_approve = false`, and audit events
`PREVIEW_FROZEN` then `NATIVE_APPROVAL_DECISION`. No credentials, account IDs,
role ARNs, bucket names, or endpoints are retained here.

## Retained-runtime identity preflight

On 2026-09-23, the `amit` profile on the existing retained host was STS-verified
as the Organizations management identity and its active Organizations mapping
contained all four registered LAB aliases: `lab-dev`, `lab-poc`,
`lab-qa`, and `lab-sec`. Region selection is fixed to `ap-southeast-1`. The
`vagent` profile is present but resolves to a member-account context and its
Organizations lookup fails with `AWSOrganizationsNotInUseException`; it is not
used for this control.

The live operator service previously had no explicit `SECOPS_LAB_PROFILE`
override and therefore selected `vagent` by default. The PR deployment script
now pins the operator's exact service drop-in to `amit` and checks the running
process environment before declaring readiness. The bounded repo-owned
deployment completed on 2026-09-22 and restarted only the Operator and LibreChat
services on the existing host. No AWS resource, IAM, OIDC, networking, or
remediation state was changed. A fresh AWS MCP identity/host preflight on
2026-09-23 reconfirmed the exact personal-LAB management identity, Region,
retained host ownership, running state, and SSM availability without publishing
raw identifiers.

An independent sparse checkout of the public LibreChat `v0.8.8-rc1` tag
confirmed the reviewed `resume.js` SHA-256
`6f0f53afbaa06dd65e9558e1595060433e37952ef9b0ad1d4ad57781bcbcf025` and
deterministic patched digest
`311b925b5157aa22fff9fd846ed7075a043579d1ad1f4201ac5e4517dc12a77a`. The
retained runtime's semantically reviewed source variant is separately pinned
and its installed Reject-receipt patch digest was verified
`9a5ea6723b0daddf7812fba7fb03f47f76183889c3e96a6ad827972f2ad9e0a7`; source
drift fails closed. A post-restart read-only SSM check on 2026-09-23 verified
both services active, the pinned patch installed, and required private
environment values present without reading their contents. The s3_ssl read
endpoint returned HTTP 200; the four registered aliases were identity-verified
and AVAILABLE, the response was public-safe/read-only, and a current
non-compliant finding was present. Raw findings and resource identifiers were
not retained here.

Failure/recovery regression now includes racing duplicate Reject submissions
(one durable terminal decision, one fail-closed replay) and service recreation
with durable receipt-chain verification and consumed-retry rejection.

## Native E2E stop gate

Issue #195 traced the earlier 401s to the test harness, not a retained-runtime
auth/proxy defect. Its page-level `fetch()` calls sent same-origin cookies but
did not include LibreChat's `Authorization` header. The pinned upstream
LibreChat v0.8.8-rc1 auth context sets that header through its authenticated
request helpers; normal UI-generated requests included the header and
succeeded. The supported correction is therefore in the runner only; no
runtime auth, proxy, or session configuration was changed.

The fixed Playwright runner is `tests/e2e/issue191_s3_ssl_reject.mjs`; its
contract tests are `tests/issue191_browser_e2e.test.cjs`. It reads the four
alias-only live status first, waits on rendered chat state, requires one native
`s3_ssl` / Reject-only card with exactly one Reject and no Approve action,
clicks Reject and Submit once, and verifies the rendered terminal response.
It uses the exact native LibreChat message input and Send handler; status and
Reject preparation use separate Compliance Agent v1 conversations, with the
status-only conversation deleted before the approval request is sent. The runner
observes only status, route, method, and authorization-header-name presence
from ordinary application responses; it never records header values, reads
browser storage, or exports authentication. It verifies a successful
authenticated message-history reload and deletes test conversations only
through LibreChat's native conversation menu and confirmation dialog.

The native resume path is accepted only when its receipt-gated request returns
HTTP 200/201; the runtime boundary verifies the durable Reject receipt and
fresh unchanged provider readback before allowing continuation. Exact control
and scope binding remain server-side receipt/reconciliation assertions, not
private browser-state inspection. The updated local Node contract suite passes
8/8.

The authenticated LibreChat native card/resume test remains the acceptance
gate. The repo-owned Reject-only integration is deployed, but no native
`s3_ssl` card or decision has yet been created. The isolated localhost-CDP
session was reattached through Windows Node; normal app auth refresh and
message-history calls returned HTTP 200. The exact read-only diagnostic
conversation remains in the UI because its native DELETE returned HTTP 401
before refresh and HTTP 500 after refresh. Redacted SSM logs attribute the 500
to the conversation-store delete stage but reveal no safe exception class; no
direct database cleanup was attempted. No password, cookie, token, or browser
database was read or exported. Do not test Approve. Until supported cleanup,
the native Reject, durable receipt, zero-dispatch evidence, fresh unchanged
provider readback, and reconnect/recovery checks are proven, PR #192 remains
draft and Issue #191 remains open. `scripts/check.sh` passed 336 tests (4
skipped) before the current runner update; rerun it before handoff. The default
worktree had no MCP SDK installed initially; no dependencies were added to the
repository.
