# AWS SecOps Platform Phase 1 3–5 minute demo

## Setup before the audience joins

```bash
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 ./scripts/pilot-v1.sh rearm-sg
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 ./scripts/pilot-v1.sh serve
```

Open `http://localhost:3340/`.

## Story

“This is a small AWS SecOps platform in a personal lab. It normalizes multiple
finding sources, routes each to a specialist, and permits only one exact,
human-governed AWS remediation.”

1. Import `examples/cloudscape-synthetic.json` as **CloudSCAPE-style**.
   - Show `Compliance Agent`, `PLAN_ONLY`, and `provider verification = NOT_PERFORMED`.
2. Import `examples/vapt-synthetic.csv` as **VAPT-style**.
   - Show `Vulnerability Agent`, `PLAN_ONLY`, and both sources in one backlog.
3. Click **Check real SG**.
   - Point to real provider evidence: public TCP/22 and `NON_COMPLIANT`.
   - Contrast `REMEDIATION_SUPPORTED` with the imported plan-only records.
4. Click **Reject**.
   - Point to `Policy = NOT_CALLED`, provider unchanged, and no AWS change.
5. Click **Policy DENY test**.
   - Explain that this is synthetic `prod` input, not an AWS production account.
   - Point to native `DENY`, provider unchanged, and no AWS change.
6. Click **Approve DEV**.
   - Point to human `APPROVE`, Policy `ALLOW`, the exact remediation tool, and
     independent provider verification `COMPLIANT`.
7. Click **Read S3 assessment**.
   - Show two allowlisted buckets, ten provider checks, and the one safe
     versioning exception.
   - Point to the management backlog and its recommended focus.
   - Point to `NOT_REQUIRED` human decision and `changed AWS = false`.
8. Download the CSV or Markdown action plan and show that source, specialist,
   eligibility, priority, recommendation, and status come from the same
   management backlog.

## Close

“Adapters normalize evidence; deterministic code routes specialists and action
eligibility. The model explains but does not authorize. Human intent, Policy,
exact tools, and provider readback remain separate controls.”

Stop the local UI with `Ctrl+C`. Retain the inexpensive AWS demo resources.
