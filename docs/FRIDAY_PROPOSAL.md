# Friday management proposal — AWS Copilot

Status: Phase 0A draft

Audience: operations, development, security/compliance management

Goal: win approval for a bounded technical pilot, not claim a finished production platform.

## Slide 1 — Problem

**AWS operations are scaling faster than manual compliance remediation.**

- Many AWS accounts, resources and recurring security/compliance findings.
- Teams spend time reading findings, identifying the correct resource, deciding remediation, executing changes and proving closure.
- The same control patterns repeat across accounts and services.
- Manual work creates delay, inconsistency and weak evidence trails.

Message:

> We do not need another scanner. AWS already produces findings and provider state. We need a governed way to understand, approve, remediate and verify them faster.

## Slide 2 — What we already proved

The existing AgentCore R&D demo has already shown a real end-to-end governance pattern:

```text
real AWS Security Group finding
-> human ASK / Approve / Reject
-> AgentCore Gateway
-> AgentCore Policy ALLOW / DENY
-> exact remediation
-> AWS provider re-read
-> COMPLIANT
```

This is not yet the final product architecture, but it proves the core governance concept.

## Slide 3 — Proposed solution

**AWS Copilot**

```text
AWS provider findings / state
        |
        v
specialist agent
        |
        v
human decision when needed
        |
        v
AgentCore Gateway + deterministic Policy
        |
        v
exact governed remediation tool
        |
        v
provider verification + audit
```

Initial specialists:

- **Compliance Agent** — Security Groups, S3, IMDSv2, Config/Security Hub context.
- **Vulnerability Agent** — Inspector/ECR findings and remediation evidence.

The model recommends and explains; IAM + Policy + exact tools remain the hard security boundary.

## Slide 4 — How it could scale

Proposed company pattern:

```text
central security/tooling account
        |
        v
AgentCore Harness / Gateway / Policy
        |
        v
STS AssumeRole
        |
        +--> AWS account A
        +--> AWS account B
        +--> ... many accounts
```

Key design principles:

- provider-native findings instead of custom scanners;
- exact read/remediation tools instead of generic AWS mutation access;
- human approval for sensitive mutations;
- provider verification after action;
- compact audit evidence;
- later Organizations/StackSets for onboarding at scale.

## Slide 5 — Proposal / ask

**Request: approve a bounded non-production technical pilot.**

Before a production decision we will validate:

1. AgentCore Harness/Runtime/Gateway/Policy behavior in our Region;
2. Bedrock model availability, quality and cost;
3. one or two real controls in an isolated lab;
4. cost at realistic scale;
5. workload IAM and cross-account pattern;
6. audit and human-approval design.

Current personal lab gives us an isolated low-cost place to learn before touching company environments.

## Management questions we should be ready to answer

### Why AI?

Because findings are heterogeneous and need explanation, context, prioritization and operator interaction. Deterministic Policy/IAM still controls the action.

### Why AgentCore?

It provides AWS-native agent execution/governance building blocks so we do not need to build every agent loop, gateway, policy and observability capability ourselves.

### Is this autonomous remediation?

Not initially. Sensitive actions remain human-approved and Policy-governed.

### Does it replace Security Hub / Config / Inspector?

No. It consumes provider truth and turns it into governed remediation and verified evidence.

### Is it production-ready now?

No. The governance concept is proven; the clean architecture, model choices, Region behavior, cost and organization-scale deployment still need a bounded technical pilot.

## Friday demo recommendation

Do **not** spend the week rebuilding the entire clean product.

Use the existing working R&D demo to show the wow factor, then use this proposal to explain how the clean product would be built after approval.

The strongest sequence is:

```text
1. show real SG problem
2. show human approval
3. show AgentCore Policy ALLOW / DENY
4. show real remediation + verification
5. switch to proposed architecture / scale / next-step slide
```
