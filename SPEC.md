# Specification

Status: approved — Phase 0A / Issue #1

## Problem

We have a working AgentCore governance R&D demo, but management approval is not yet secured and the clean product architecture still has new-service, Region, model, scale, and cost questions.

The immediate need is a technically honest **proposal and decision baseline**, not another rushed full implementation before Friday.

## Scope

Produce a management-ready AWS Copilot proposal that clearly separates:

- what the R&D demo has already **PROVEN**;
- what the clean product **PROPOSES**;
- what the next standalone personal-lab milestone must **VALIDATE**.

## MUST

- Explain the problem, proposed value, governance story, architecture, phased deployment path, and next validation questions.
- Keep AgentCore Harness -> MCP Gateway -> Policy -> exact governed tools -> workload IAM/STS -> provider verification as the proposed direction.
- Record the standalone personal `vagent` account as the preferred isolated R&D lab for follow-on experiments.
- Define concrete scale/cost scenarios, including 1,000 and 20,000 S3 buckets with five controls and a monthly 20-EC2 workflow.
- Keep model choice replaceable; include Nova 2 Lite and stronger candidates in the next benchmark plan.
- Keep the repository public-safe: no private AWS environment identity or secrets committed.

## MUST NOT

- Deploy the full clean product runtime in this PR.
- Claim Harness/Registry/model/Region behavior that has not been validated.
- Treat promotional credit as proof that a service is free.
- Build multi-account onboarding, second controls, broad security-service rollout, Temporal Policy, WAF, Registry, StackSets, Supervisor/A2A, or EKS here.
- Copy old R&D plumbing wholesale.
- Commit account IDs, environment ARNs, credentials, tokens, private endpoints, emails, or private evidence.

## Verification

The PR is accepted when a reviewer can answer, from repository docs alone:

1. What problem are we proposing to solve?
2. What has already been demonstrated?
3. What architecture are we proposing?
4. What is still unknown?
5. What should be tested next in the personal lab?
6. What scale/cost questions must be answered before a company pilot?
7. What is the Friday management ask?

No AWS mutation is required for Phase 0A acceptance.

## Stop Gates

Stop for owner/controller review if work starts implementing the full product, changes the proposed security boundary materially, uses company/production AWS, or exposes private environment data.