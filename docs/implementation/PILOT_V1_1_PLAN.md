# Pilot v1.1 implementation plan

Status: active — M1–M3 PASS; M4–M5 in progress

Authority: Issue #7

Base: Pilot v1 merged through PR #6

## Goal

Extend the proven single-resource governed Pilot into a small operations-facing compliance backlog workflow without broadening the AWS mutation boundary.

```text
bounded findings
-> common contract
-> backlog summary
-> allowlisted multi-bucket S3 read
-> exception-focused AI explanation
-> management remediation plan/export
```

## M1 — One-command smoke validation

Add the smallest repeatable validation path for the existing Pilot:

- SG finding;
- Reject -> no change;
- Policy DENY -> no change;
- Approve DEV -> provider COMPLIANT;
- S3 baseline works;
- restore the dedicated demo SG to NON_COMPLIANT for the next run.

Testing must stay proportional: API/provider proof first; at most one Playwright/browser smoke when it materially helps; no browser-testing framework or Postman collection.

## M2 — Common finding contract

Add one small internal finding schema with fields such as source, resource type/id/name, environment, control, severity, status, evidence and recommendation.

Support bounded sanitized JSON/CSV import. Map the existing SG and S3 findings into the same contract. Do not add live CloudSCAPE/VAPT/Security Hub/Inspector integrations in this milestone.

## M3 — Management compliance backlog view

Extend the single-user UI/report so management can see, at minimum:

- total open findings;
- high/critical count;
- source/resource-type grouping;
- highest-priority or oldest findings;
- recommended focus.

Provider/source data remains authoritative. AI may summarize only the bounded finding set.

## M4 — Allowlisted multi-bucket S3 assessment

Extend the read-only S3 baseline to an operator/server-owned allowlist of demo/test buckets.

- no account-wide arbitrary discovery by the model;
- no model-selected bucket names;
- no S3 mutation;
- bounded volume/concurrency;
- aggregate bucket/control PASS/FAIL counts;
- send only failures/exceptions to AI explanation where practical.

## M5 — Remediation plan / management export

Produce one lightweight action-plan export from the same backlog, using fields such as finding, priority, recommended fix, optional owner/team, approval-required, status and optional target date/quarter.

Prefer CSV plus Markdown/HTML summary. Do not build a reporting platform.

## Boundaries

Do not add:

- another AWS remediation action;
- multi-account/Organizations/StackSets;
- production/company access;
- Registry or Temporal Policy rollout;
- multi-user auth;
- broad Security Hub/Config/Inspector enablement;
- EKS, Supervisor/A2A;
- generic AWS MCP/CLI write capability;
- large Playwright/Postman/E2E framework.

## Working style

- One Issue + one PR for M1–M5.
- Commit milestone-by-milestone.
- Reuse Pilot v1 code and retained lab resources.
- Use AWS MCP / official AWS docs for current behavior and direct AWS CLI for simple setup/readback.
- Small change -> exact proof -> provider readback.
- Keep public Git free of private account IDs, ARNs, endpoints, credentials, raw private evidence or company data.

## Final acceptance

Pilot v1.1 is complete when the same PR proves:

```text
bounded findings
-> common contract
-> backlog summary
-> allowlisted multi-bucket read-only assessment
-> exception-focused AI explanation
-> management remediation plan/export
```

while preserving the existing governed SG remediation path and proportional validation.
