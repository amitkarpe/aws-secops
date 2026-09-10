# Phase 4 — durable governed remediation jobs

Issue #15 / PR #16. M1–M5 PASS; ready for review.

## What changed

- Direct SG check now creates/reuses one pending job for the exact eligible
  provider finding. Its stable finding ID, job ID, DEV environment, action and
  expected postcondition are server-owned. Config and imported evidence cannot
  create jobs. Explicit backlog job creation rechecks the fixed provider first.
- Exact preview and job history in the existing thin UI. Decisions require
  the exact job ID plus REJECT, APPROVE or synthetic DENY_TEST; callers cannot
  supply tools, AWS resources, Regions or action arguments. The old approval
  endpoint now also requires an exact job ID, so it cannot bypass jobs.
- Reject is terminal without a Gateway call. Approval consumes the pending job
  durably before any network operation. A fresh matching NON_COMPLIANT provider
  read precedes the retained exact Gateway action; matching independent
  COMPLIANT readback is required for COMPLETED. No new Lambda/IAM/tool deployed.
- Generic Gateway/tool errors produce FAILED, not false Policy DENY. Unknown
  post-dispatch effect is null/UNKNOWN, not changed=false. An observed mutation
  followed by failed verification remains FAILED with changed=true.
- Job journal uses atomic mode-600 local JSON alongside the existing backlog:
  default `~/.local/state/aws-secops/backlog.jobs.json`, maximum 100 jobs/256 KB.
  The server-side PILOT_BACKLOG_FILE selects the companion path. No browser path.
  Corrupt stores stop startup; capacity exhaustion preserves history.
- Restart reads history only. Interrupted EXECUTING jobs become FAILED with an
  unknown outcome; no network calls or automatic retries. Terminal IDs cannot
  be reused. A new provider check/manual job is required for another attempt.

## Live proof

Run from the repo, with no other writer using the same local store:

```bash
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 ./scripts/pilot-v1.sh jobs-smoke
```

The versioned runner verifies private identity/profile/Region and retained
Gateway Policy ENFORCE, checks that the fixed demo SG is unattached, rearms if
needed, owns two sequential loopback child servers, proves all three outcomes
and replay rejection, restarts and compares exact persisted job records, then
restores the dedicated demonstration state. It does not deploy anything.

```text
POLICY_MODE=ENFORCE
PILOT_V1_REARM=PASS
PILOT_SG_STATUS=NON_COMPLIANT
PILOT_SG_ATTACHMENTS=0
JOB=REJECTED REPLAY=BLOCKED POLICY=NOT_CALLED CHANGED=False PROVIDER_AFTER=NOT_READ
JOB=DENIED REPLAY=BLOCKED POLICY=DENY CHANGED=False PROVIDER_AFTER=NON_COMPLIANT
JOB=COMPLETED REPLAY=BLOCKED POLICY=ALLOW CHANGED=True PROVIDER_AFTER=COMPLIANT
PLATFORM_PHASE4_JOBS_SMOKE=PASS RESTART=PASS NO_AUTOMATIC_REPLAY=PASS
PILOT_V1_REARM=PASS
PILOT_SG_STATUS=NON_COMPLIANT
PILOT_SG_ATTACHMENTS=0
```

Reject reports NOT_READ honestly: the next separate check verified the SG
still NON_COMPLIANT. DENY was returned by the retained Gateway Policy. The
approved exact Lambda returned its change result and an independent Gateway
read verified COMPLIANT. This proves the request/action/provider chain; a
separate CloudWatch invocation-count measurement was not performed.

Actual AWS changes: exact public TCP/22 rule revoke during DEV approval, then
restoration of that one rule on the fixed unattached demo SG. No new AWS
resources, IAM permissions, Gateway tools, service configuration or second
action. Three Harness SG explanations used the retained model; no new recurring
infrastructure, and cost was not separately metered. All resources retained.

## Amit's UI steps and expected results

Start with `AWS_PROFILE=amit AWS_REGION=ap-southeast-1 ./scripts/pilot-v1.sh serve`
and open `http://localhost:3340/`. This is the AWS SecOps thin UI, **not
LibreChat**. No agent reconfiguration or login is required.

1. Click **Check SG + preview job**. For the rearmed demo, expect NON_COMPLIANT
   and a PENDING job. Scroll to **Governed remediation jobs** to review resource,
   provider evidence, exact remove_unrestricted_ssh action, DEV, and postcondition.
2. Click **Reject job**. Expect REJECTED / Policy NOT_CALLED / changed=false.
   Approve becomes disabled for that terminal job; no fresh verification is claimed.
3. Click **Check SG + preview job** again, then **Synthetic Policy DENY test**.
   Expect DENIED / Policy DENY / changed=false / provider NON_COMPLIANT. This
   sends only synthetic prod input to the personal lab Gateway, not a prod account.
4. Check again, then **Approve exact DEV job**. Expect COMPLETED / Policy ALLOW /
   changed=true / provider COMPLIANT. This step changes the dedicated demo SG.
5. Reload or restart. Select any saved result in **Job history**. Same audit;
   terminal jobs cannot be approved again. Historical COMPLIANT is evidence at
   completion time, not a claim that the current SG still has that status.
6. To prepare another approved demo, run `./scripts/pilot-v1.sh rearm-sg` with
   the same AWS context. It verifies the dedicated SG is unattached and restores
   only the known demonstration rule. No automatic reset runs on app startup.

## Validation and boundaries

45 deterministic tests pass. Focused additions cover eligibility, single-use
decision, no-call Reject, failed-save before dispatch, interrupted restart,
unexpected tool errors, failed verification, bounded/corrupt history and replay.
Existing Phase 3 backlog/plan tests still pass.

One browser smoke checks retained REJECTED/DENIED/COMPLETED previews, disabled
terminal approval, reload and console exceptions. Live mutation is exercised
by the API proof, not repeated in the browser. Private screenshot/script stay
under `/home/user/.AGENTS-temp/aws-secops/platform-phase4/`, outside public Git.

```text
PLATFORM_PHASE4_BROWSER=PASS HISTORY=REJECTED,DENIED,COMPLETED TERMINAL_APPROVE_DISABLED=PASS RELOAD=PASS CONSOLE_ERRORS=0
HTTP_IDLE_SOCKET=PASS
```

The first browser attempt stalled; a GNOME Keyring creation prompt was also
reported, but its originating client was not proven. The same bounded browser
scenario passed after configuring the fresh no-login test profile with
`--password-store=basic` and bounding idle HTTP connections to five seconds.
No normal browser, GNOME Keyring, Codex credentials or shared auth settings
were changed. Basic password storage is only for this disposable no-login
test profile, not a recommendation for a real credential-bearing browser.

The socket change retains single-writer execution (no threading introduced);
an independent live idle-connection/API read passed. Python documents the
preopened-browser-socket problem for HTTPServer; Chromium documents automatic
Linux password-store selection and the explicit test-profile override:

- [Python HTTP server documentation](https://docs.python.org/3/library/http.server.html)
- [Chromium Linux password storage](https://chromium.googlesource.com/chromium/src/+/HEAD/docs/linux/password_storage.md)

Single process per store; no cross-process locking, automatic job eviction,
scheduler, retry or distributed transaction with AWS. If persistence fails
after dispatch, inspect provider state before creating any new job. A crash can
leave an unknown outcome even if the provider action succeeded. Do not convert
that uncertainty into a successful result or a silent retry.
