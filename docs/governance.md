# Governance

The central design rule is:

> **The model is an assistant, not the authorization boundary.**

Demo v1 deliberately splits governance across independent layers.

## 1. Topic scope

The AWS Compliance Agent is a specialist assistant. Its instructions limit it to deployed AWS compliance operations and directly relevant education.

This boundary improves usability and reduces accidental tool use, but it is **not** the hard AWS authorization control.

## 2. Read-only vs execution intent

A request to read, check, explain, summarize, recommend or plan must stay read-only.

Only an explicit current request to fix/apply/execute can move into remediation preparation.

That distinction prevents a recommendation from silently becoming an AWS change.

## 3. Server-owned scope

The model cannot choose arbitrary execution parameters.

The server owns:

- supported controls;
- retained resource manifests;
- eligible resource intersection;
- exact remediation action;
- immutable batch identity and approval data.

A caller/model-supplied resource ID is not enough to expand the blast radius.

## 4. Human approval

S3 and Security Group changes remain independently approved.

```text
S3 request -> Approve / Reject
SG request -> Approve / Reject
```

If a UI presents both decisions together, the submission is only batching the two independent decisions. There is no session-wide approval.

Approval means: **this exact request may proceed to the next governance layer**. It does not mean the change succeeded.

## 5. Gateway + Policy

After approval, the bounded executor invokes AgentCore Gateway. Policy independently evaluates the exact invocation.

This creates an important separation:

- model recommendation is not authorization;
- human approval is not Policy ALLOW;
- Policy ALLOW is not provider success.

Each layer answers a different question.

## 6. Exact tools

Demo v1 exposes narrow tools for only the supported actions.

It intentionally does **not** expose a generic model-driven AWS CLI/API mutation surface.

Execution-time account, Region, API, action and target scope are bounded by server configuration and current provider guards.

## 7. Provider verification

After mutation, AWS is read again.

A job may be reported completed only when direct provider state matches the approved target. `FAILED` and `UNKNOWN` remain explicit outcomes.

AWS Config is independent compliance evidence and may update later.

## Evidence sources

| Question | Authoritative evidence |
|---|---|
| Did an AWS API call happen? | CloudTrail |
| What did the executor log? | CloudWatch Logs |
| What does the compliance rule report? | AWS Config |
| What is the resource state now? | Direct provider readback |
| What did the workflow approve/track? | Durable batch/approval state |
| What did Policy decide? | Gateway/Policy evidence |

A future Operations Console should correlate these sources, not replace them.

## Public safety

This repository is public. Never publish credentials, account IDs, private ARNs/endpoints, auth material, session IDs, raw private findings or private screenshots.
