# Roadmap

## Completed

- Demo v1 retained-resource S3/SSH governance and provider-verification proof.
- Four-account provider E2E and organization AWS Config evidence.
- Four-account bounded remediation path with separate approval, fixed execution path, provider readback and independent Config convergence.
- Unified Config Dashboard and four-account demo re-arm.
- Legacy 100-S3 / 10-SG Operator path retired from the active product surface.
- Read-only `aws_secops_operator` AgentCore Harness experiments and contextual investigation milestones.
- Issue #68 is closed; its original two-account prerequisite is no longer the current roadmap gate.
- Compliance Agent v1 implemented as a clean isolated AgentCore Harness-backed specialist.
- Compliance Agent v1 live E2E: Config 4×2 checks, five golden prompts, one-tool MCP, LibreChat authenticated smoke, zero mutation.

## Current

### Compliance Agent v1 release closure

- make LibreChat access reproducible rather than relying on one-off ACL repair;
- keep a real stdio MCP initialization regression in CI;
- publish immutable GitHub Release `compliance-agent-v1.0.0`;
- close Issues #123/#125 after release evidence is verified.

### Scalable Ops UX + governed exceptions — Issue #140

Issue #140 is the future master roadmap for:
- rich inline Ops cards;
- CSV/export;
- deterministic one-time exclusions;
- managed exception registry and expiry;
- 50+ account pagination/filter/query contracts;
- Artifact analytics;
- Jira integration;
- exception governance/audit lifecycle;
- large-scale performance acceptance.

Do not implement all of #140 as one change. Choose one bounded milestone at a time.

First bounded exception milestone: **Issue #141**.

Issue #141 plans exact one-time exclusions for the current two controls only:
- `Fix all S3 findings except bucket X`;
- `Fix restricted SSH except security group Y`.

Required rule:

`discovered_set - excluded_set = included_set`

The approval view must show included and excluded resources before execution. Excluded resources remain truthful AWS findings and are never reported as fixed.

### Read-only AWS MCP evidence source — Issue #130

Evaluate the already-proven persistent read-only AWS MCP for investigation/evidence only:

- Config;
- S3 posture;
- Security Group posture;
- Inspector;
- CloudTrail Event History;
- IAM/resource inventory.

It must not bypass the existing governed mutation path.

## Later

- managed/persistent exception registry with owner, reason, approval, expiry/review date and Jira/change reference;
- rich MCP UI resources and CSV export for large Ops result sets;
- 50+ account / 100k-finding scale contracts with server-side pagination/filtering;
- structured operational event ledger for exact agent-mediated change history;
- AgentCore Memory for conversational/episodic continuity, not authoritative audit;
- Bedrock Knowledge Bases/RAG when unstructured runbooks, SOPs, policies and incident narratives justify semantic retrieval;
- broader AWS Ops Agent only after stable specialist contracts are proven;
- additional controls only when justified by operator value and reviewed as separate milestones.

## Publication assurance

Before broader promotion:

- review reachable history for accidental sensitive material;
- decide/document repository licensing and reuse intent;
- improve repository About metadata.

No 1,000-live-resource milestone is planned for Demo v1.
