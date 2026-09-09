# Pilot v1 operator runbook

## Purpose

Run the retained single-user Compliance Agent demo without discovering or
selecting arbitrary AWS resources. The private state file binds the app to one
Harness, Gateway, Policy engine, demo Security Group, and demo S3 bucket.

## Prerequisites

- repository root is the current directory;
- AWS profile `amit` is authenticated;
- Region is `ap-southeast-1`;
- `/home/user/.AGENTS-temp/aws-secops/pilot-v1/state.json` exists with mode
  `600` and came from the Pilot deployment;
- port `3340` is free or already owned by this repository.

## Start a clean demo

The first command verifies identity/Region, confirms the dedicated Security
Group is unattached, and restores only its exact public TCP/22 demo rule:

```bash
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 ./scripts/pilot-v1.sh rearm-sg
```

Expected terminal markers:

```text
PILOT_V1_REARM=PASS
PILOT_SG_STATUS=NON_COMPLIANT
PILOT_SG_ATTACHMENTS=0
```

Start the loopback UI:

```bash
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 ./scripts/pilot-v1.sh serve
```

Open `http://localhost:3340/`. Keep the terminal open; use `Ctrl+C` to stop
only this local UI. AWS resources remain retained for the next demo.

## Quick health checks

```bash
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 ./scripts/pilot-v1.sh status
curl --fail --silent http://localhost:3340/api/state | jq '{stage,message}'
./scripts/check.sh
```

## Expected visible flow

1. **Check real SG** -> `FINDING`, provider `NON_COMPLIANT`, change `false`.
2. **Reject** -> `REJECTED`, Policy `NOT_CALLED`, provider unchanged.
3. **Policy DENY test** -> `DENIED`, native Policy `DENY`, provider unchanged.
4. **Approve DEV** -> `COMPLETED`, Policy `ALLOW`, provider `COMPLIANT`,
   changed AWS `true`.
5. **Read S3 baseline** -> five visible `PASS` controls, Policy `ALLOW`,
   changed AWS `false`.

If the exact Security Group is already compliant, rerun `rearm-sg` before the
demo. Do not manually replace resource IDs or broaden the tools.

## Failure boundary

Stop if the profile, account, or Region does not match private Pilot state; the
demo Group has an attachment; Policy is not ENFORCE/ACTIVE; the exact tool is
missing; or provider verification disagrees with the UI. A transport response
alone is not a PASS.
