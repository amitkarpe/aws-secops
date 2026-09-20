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
