# Roadmap

## Now — Phase 0A: proposal

- Management-ready Friday story.
- Future-state AgentCore architecture baseline.
- Clear PROVEN vs PROPOSED vs TO VALIDATE boundary.
- Technical validation backlog.
- Scale/cost scenarios and phased deployment proposal.

## Next — Phase 0B: personal-lab feasibility

Use the isolated standalone personal lab account to validate, with small bounded experiments:

1. AgentCore feature/Region reality in Singapore.
2. Harness vs Runtime behavior and smallest governed tool path.
3. Gateway/Policy/Lambda MCP behavior.
4. Bedrock model availability and a small Nova 2 Lite vs stronger-model benchmark.
5. Cost/scale estimates for S3 compliance and EC2 vulnerability/remediation scenarios using current official pricing.
6. Hosting/retained-resource cost and cleanup behavior.

## After management/pilot approval

1. **Clean vertical slice** — Compliance Agent, real Security Group, human approval, governed exact remediation, provider verification.
2. **Organizations foundation** — approved accounts, STS roles, server-owned routing, StackSet design.
3. **Compliance breadth** — S3 Block Public Access, EC2 IMDSv2, Security Hub/Config where useful.
4. **Vulnerability Agent** — real Inspector/ECR findings; manual specialist switching.
5. **Policy-visible approval** — trusted approval event and Temporal Policy.

## Later

- Registry catalog/discovery when reuse becomes a real problem.
- A2A Supervisor only when manual switching becomes a measured usability problem.
- Native WAF/rate limits/evaluations/optimization as hardening, not initial plumbing.
