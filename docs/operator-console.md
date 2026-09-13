# Operations Console direction

The current Operator homepage and raw `/bulk` batch view were built primarily for Demo v1 preparation, status and engineering troubleshooting.

They are useful, but the long-term value is not a second place to perform arbitrary AWS changes.

## Long-term role

Evolve the Operator UI into an **Operations Console** for platform support and evidence correlation.

A useful future home page could summarize:

- current compliance/remediation workload;
- active, completed, failed and unknown jobs;
- S3 / SG control health;
- AWS Config, Gateway/Policy and executor health;
- recent approvals and verification state.

## Remediation history

Replace raw batch IDs as the primary UX with a human-facing remediation/job identity while preserving the immutable batch details underneath.

Example:

```text
REM-1842  S3 BPA        100 resources   COMPLETED
REM-1841  Restricted SSH 10 resources   COMPLETED
REM-1840  S3 BPA         50 resources   REJECTED
```

A detail view can then correlate:

- finding / control;
- exact owned scope;
- recommendation;
- approver and decision time;
- Policy result;
- executor/tool version;
- provider verification;
- Config convergence;
- links to CloudTrail / CloudWatch evidence.

## Troubleshooting and health

The console should make support questions fast to answer:

- Is AWS Config recording successfully?
- Is the delivery channel healthy?
- Is Gateway/Policy reachable?
- Which job is RUNNING, FAILED or UNKNOWN?
- Did provider verification complete?
- Which version/commit is deployed?

## Evidence model

The console should **aggregate and correlate**, not replace AWS evidence systems.

| Evidence | Source of truth |
|---|---|
| AWS API activity | CloudTrail |
| Executor/runtime logs | CloudWatch Logs |
| Compliance evaluation | AWS Config |
| Current resource state | Direct provider readback |
| Workflow/approval state | Durable application journal |
| Policy outcome | AgentCore Gateway/Policy evidence |

A future correlation ID should make one remediation easy to trace across these systems.

## Safe admin actions

Potential long-term console actions should remain narrow, for example:

- refresh provider verification;
- reconcile an `UNKNOWN` job by readback;
- refresh Config status;
- open CloudWatch/CloudTrail evidence;
- view immutable plan / approval data;
- archive completed workflow records according to retention policy.

The console must **not** become a generic selector for arbitrary accounts, resources, APIs or AWS mutations.

## Current Demo v1

For now:

- the main Operator page is the friendly demo/status view;
- `/bulk` remains an advanced/engineering detail view;
- normal remediation approval stays in the AWS Compliance Agent chat;
- the runtime is frozen while public documentation and reviewer feedback are collected.
