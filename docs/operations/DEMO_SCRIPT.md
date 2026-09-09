# Pilot v1 3–5 minute demo

## Setup before the audience joins

```bash
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 ./scripts/pilot-v1.sh rearm-sg
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 ./scripts/pilot-v1.sh serve
```

Open `http://localhost:3340/`.

## Story

“This is a single Compliance Agent in a personal AWS lab. It can read two fixed
demo resources and perform only one exact, human-governed remediation.”

1. Click **Check real SG**.
   - Point to real provider evidence: public TCP/22 and `NON_COMPLIANT`.
   - Point to the agent explanation and `changed AWS = false`.
2. Click **Reject**.
   - Point to `Policy = NOT_CALLED`, provider unchanged, and no AWS change.
3. Click **Policy DENY test**.
   - Explain that this is synthetic `prod` input, not an AWS production account.
   - Point to native `DENY`, provider unchanged, and no AWS change.
4. Click **Approve DEV**.
   - Point to human `APPROVE`, Policy `ALLOW`, the exact remediation tool, and
     independent provider verification `COMPLIANT`.
5. Click **Read S3 baseline**.
   - Show the five provider-backed PASS controls.
   - Point to `NOT_REQUIRED` human decision and `changed AWS = false`.

## Close

“The model explains findings; it does not decide authorization or invent AWS
state. Human intent, deterministic Policy, exact tools, and provider readback
are visible as separate controls.”

Stop the local UI with `Ctrl+C`. Retain the inexpensive AWS demo resources.
