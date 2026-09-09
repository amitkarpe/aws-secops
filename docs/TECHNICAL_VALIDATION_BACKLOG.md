# Technical validation backlog

Status: Phase 0A proposal input; execute in the follow-on personal-lab milestone

Purpose: convert unknown AgentCore/Bedrock assumptions into small measurable experiments before a company pilot.

## 1. Region and service reality

Validate current support and practical behavior in `ap-southeast-1` for:

- AgentCore Harness;
- Runtime;
- Gateway;
- Policy;
- Identity;
- Observability / Evaluations;
- Temporal Policy;
- built-in tools where relevant;
- AWS Agent Registry availability and nearby supported Regions.

Deliverable: one compact `SUPPORTED / NOT SUPPORTED / NOT TESTED` matrix with official-source links and live evidence where useful.

## 2. Harness vs Runtime

Questions:

- What is the smallest Harness deployment for one Compliance Agent?
- Which agent-loop behavior is native to Harness?
- What still requires custom Runtime code?
- What is the deployment/rollback model?
- What is retained and billed while idle?

Deliverable: recommendation + one minimal live Harness experiment.

## 3. Gateway and Policy

Validate:

- Lambda target exposed as an MCP tool;
- exact tool schema;
- Policy ALLOW / DENY behavior;
- what context/arguments Policy can see;
- how tool identity and caller identity are represented;
- negative case: denied call must not reach the target;
- logging/audit evidence available natively.

Deliverable: one harmless governed tool experiment, not a full product.

## 4. Human approval

Validate near-term options:

- LibreChat approval UX reused from R&D;
- Harness client/inline-function handoff;
- exact point where approval becomes a trusted event;
- what is needed later for Temporal Policy visibility.

Do not implement a full temporal-approval system during feasibility.

## 5. Bedrock model matrix

Test currently accessible candidates in the personal lab.

At minimum include:

- Nova 2 Lite;
- one stronger Bedrock model available through the intended Region/routing path;
- optionally one vendor-diverse comparison if access and residency assumptions are clear.

Use the same fixed cases:

1. identify unrestricted SSH correctly;
2. distinguish compliant/no-op state;
3. select read vs remediation tool correctly;
4. explain S3 Block Public Access failure;
5. explain IMDSv2 failure;
6. refuse action when evidence is missing;
7. interpret Policy DENY correctly;
8. interpret provider verification correctly.

Measure:

- correctness;
- unsafe tool attempts;
- hallucination;
- latency;
- token use;
- estimated cost.

## 6. Hosting/deployment choices

Compare only realistic options:

- AgentCore Harness for specialist agent;
- Lambda for small exact tools;
- Runtime MCP server only when a concrete need appears;
- thin existing UI/LibreChat for pilot;
- no EKS unless later requirements justify it.

Record:

- deployment unit;
- IAM identity;
- idle/retained resources;
- operational complexity;
- estimated recurring cost;
- cleanup/rollback path.

## 7. Scale and cost model

Use current official AWS pricing and clearly state assumptions.

### S3 compliance scenarios

Assume five representative controls per bucket, for example:

- Block Public Access / no public access;
- encryption;
- versioning;
- secure transport / TLS policy;
- logging / audit requirement.

Scenarios:

```text
1,000 buckets x 5 controls = 5,000 checks / assessment
20,000 buckets x 5 controls = 100,000 checks / assessment
```

Compare:

- direct provider API assessment;
- AWS Config / Security Hub provider findings where applicable;
- weekly vs daily vs monthly frequency;
- agent reasoning only on failed/changed controls vs agent reasoning on every check.

Important hypothesis to test:

> Use deterministic/provider-native checks for bulk evaluation and spend model tokens primarily on exceptions, explanation and remediation—not on every compliant resource.

### EC2 vulnerability/remediation scenario

Baseline:

- 20 EC2 instances per month;
- consume existing Inspector/provider findings where possible;
- compare/triage findings;
- produce recommendation;
- human approval;
- bounded patch/remediation;
- provider verification.

Estimate separately:

- Inspector/security-service cost;
- model reasoning cost;
- AgentCore calls;
- remediation execution cost;
- logs/evidence storage.

## 8. Cost components to keep separate

Never present one blended number without assumptions.

Track:

1. model inference;
2. AgentCore Harness/Runtime;
3. Gateway/Policy;
4. Lambda/tool execution;
5. CloudWatch/logging/audit;
6. Security Hub / Config / Inspector where used;
7. storage/data transfer where material;
8. optional Registry/WAF/other later services;
9. UI hosting if retained.

Promotional credit is recorded separately from gross service cost.

## 9. Personal lab -> company migration

Personal feasibility should prove architecture, not create identities to migrate.

Promote later:

- source;
- IaC;
- tool schemas;
- policies;
- tests/evaluations;
- cost assumptions;
- architecture decisions.

Recreate later:

- IAM roles;
- account/OU mappings;
- resource IDs;
- keys/secrets;
- delegated administrators;
- endpoints;
- retained AWS resources.

## Exit criteria for Phase 0B

Before recommending a company non-production pilot, we should know:

- which AgentCore pieces we actually need;
- which Region constraints matter;
- which model is good enough for the first specialist;
- the smallest correct governed tool pattern;
- approximate cost at realistic scale;
- what AWS-native detection services we reuse;
- what the company pilot must deploy and what can stay deferred.
