# Governance

The central design rule is:

> **The model is an assistant, not the authorization boundary.**

Demo v1 deliberately splits governance across independent layers.

## 1. Topic scope

The AWS Compliance Agent is a specialist assistant. Its instructions limit it to deployed AWS compliance operations and directly relevant education.

This boundary improves usability and reduces accidental tool use, but it is **not** the hard AWS authorization control.

## 2. Read-only vs execution intent

A request to read, check, explain, summarize, recommend or plan is intended to stay read-only.

Only an explicit current request to fix/apply/execute can move into remediation preparation.

Recorded read-only tests/smokes produced no executor request, but this distinction is still partly an **agent-behavior instruction**. Human approval, Gateway/Policy, exact tools and IAM remain the independent AWS-change controls.

## 3. Server-owned scope

The model cannot choose arbitrary execution parameters.

The server owns:

- supported controls;
- retained resource manifests;
- eligible resource intersection;
- exact remediation action;
- immutable batch identity and approval data.

A caller/model-supplied resource ID is not enough to expand the blast radius.

Demo v1 currently uses a conservative family-complete readiness rule: a family is prepared only when the whole retained family passes the relevant readiness/eligibility gates. This is not arbitrary-subset remediation.

## 4. Human approval

S3 and Security Group changes remain independently approved.

```text
S3 request -> Approve / Reject
SG request -> Approve / Reject
```

If a UI presents both decisions together, the submission is only batching the two independent decisions. There is no session-wide approval.

Approval means: **this exact request may proceed to the next governance layer**. It does not mean the change succeeded.

The approval/batch identity binds exact workflow scope. It is not presented as a secret credential or as proof that a particular human identity is part of the later Policy decision.

## 5. Gateway + Policy

After approval, the bounded executor invokes AgentCore Gateway. Policy independently evaluates the exact invocation.

This creates an important separation:

- model recommendation is not authorization;
- human approval is not Policy ALLOW;
- Policy ALLOW is not provider success.

Each layer answers a different question.

The inspected current design constrains the bounded invocation and environment. Demo v1 does not claim that Policy itself proves who clicked the human approval button.

## 6. Exact tools

Demo v1 exposes narrow tools for only the supported actions.

It intentionally does **not** expose a generic model-driven AWS CLI/API mutation surface.

Execution-time account, Region, API, action and target scope are bounded by server configuration and current provider guards.

This claim is deliberately narrow: it describes the **model-accessible tool surface**. It is not a certification that every permission available to the retained host is least-privilege isolated from every other local process.

## 7. Provider verification

After mutation, AWS is read again.

A job may be reported completed only when direct provider state matches the approved target. `FAILED` and `UNKNOWN` remain explicit outcomes.

AWS Config is independent compliance evidence and may update later.

## What is trusted in Demo v1

Demo v1 is a personal-lab POC. Its trust model includes:

- the retained host and its deployment configuration;
- the LibreChat approval configuration;
- the reverse proxy/authentication configuration protecting operator surfaces;
- the server-owned manifests and durable local state;
- the exact Gateway/Policy/tool configuration installed for the demo.

The project does not claim hostile multi-tenant isolation, tamper-proof approval records, production identity governance or complete host-wide IAM isolation.

## Operator maintenance is a separate branch

`Prepare demo` is intentionally privileged operator maintenance. It can change the owned lab resources to the known non-compliant demo state after a confirmation and provider guards.

It is **not** exposed to the agent, is **not** normal remediation approval and should not be used as evidence that the model can reset AWS resources.

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
