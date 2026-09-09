# AWS SecOps Platform Phase 1 operator runbook

## Purpose

Run the retained single-user multi-source SecOps demo without discovering or
selecting arbitrary AWS resources. The private state file binds the provider
path to one Harness, Gateway, Policy engine, demo Security Group, and bounded
S3 allowlist. Synthetic source imports remain plan-only.

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

Phase 2: open `http://localhost:3340/` and click **Sync AWS Config**. Expect
`SOURCE_SYNCED`, SUCCESS (or explicitly PARTIAL), provider observation/sync
times, Compliance Agent explanation, and PLAN_ONLY. The verified snapshot had
three findings; live counts can change. Approve stays disabled. Download CSV
or Markdown to inspect the same records. No agent reconfiguration is needed.

With the app running, the Phase 2 read-only acceptance command is:

```bash
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 ./scripts/pilot-v1.sh provider-smoke
```

Expected: `PLATFORM_PHASE2_PROVIDER_SMOKE=PASS`. It performs no SG reset or
remediation. ERROR retains prior evidence and last-success time; resolve local
access/Harness availability before retrying. Restarting clears the in-memory
snapshot. Config INFO severity means unspecified; a recent sync does not make
an old evaluation current.

```bash
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 ./scripts/pilot-v1.sh status
curl --fail --silent http://localhost:3340/api/state | jq '{stage,message}'
./scripts/check.sh
```

The proportional live regression is one command. It starts its own ephemeral
loopback server, imports and routes both synthetic formats, proves plan-only
cannot mutate, performs the governed SG and S3/API sequence, validates the
backlog and both exports, stops the server, and restores the dedicated SG:

```bash
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 ./scripts/pilot-v1.sh smoke
```

## Expected visible flow

1. Select **CloudSCAPE-style compliance**, choose
   `examples/cloudscape-synthetic.json`, and click **Import source**. Expect
   `Compliance Agent` and `PLAN_ONLY`.
2. Select **VAPT-style vulnerability**, choose `examples/vapt-synthetic.csv`,
   and click **Import source**. Expect `Vulnerability Agent` and `PLAN_ONLY`.
3. **Check real SG** -> `FINDING`, provider `NON_COMPLIANT`, eligibility
   `REMEDIATION_SUPPORTED`, change `false`.
4. **Reject** -> `REJECTED`, Policy `NOT_CALLED`, provider unchanged.
5. **Policy DENY test** -> `DENIED`, native Policy `DENY`, provider unchanged.
6. **Approve DEV** -> `COMPLETED`, Policy `ALLOW`, provider `COMPLIANT`,
   changed AWS `true`.
7. **Read S3 assessment** -> two allowlisted buckets, ten controls, nine
   `PASS`, one versioning `FAIL`, Policy `ALLOW`, changed AWS `false`.
8. Review source/specialist/eligibility groupings, then download **action plan CSV** or
   **summary Markdown** from the same open findings.

If the exact Security Group is already compliant, rerun `rearm-sg` before the
demo. Do not manually replace resource IDs or broaden the tools.

## Failure boundary

Imported source evidence is never AWS provider verification and exposes no
Approve action. Stop if the profile, account, or Region does not match private Pilot state; the
demo Group has an attachment; Policy is not ENFORCE/ACTIVE; the exact tool is
missing; or provider verification disagrees with the UI. A transport response
alone is not a PASS.
