# Roadmap

## Now — MVP-1

- Compliance Agent on AgentCore Harness in Singapore.
- Exact Security Group read/remediation Lambda MCP tools behind Gateway Policy.
- One real provider-verified SSH compliance lifecycle in a member dev/sandbox account.

## Next

1. **Organizations foundation** — 2–3 approved accounts, STS read/remediation roles, server-owned routing, StackSet design.
2. **Compliance breadth** — S3 Block Public Access and EC2 IMDSv2; use Security Hub/Config only where they add provider value.
3. **Vulnerability Agent** — real Inspector/ECR findings; manual agent switching.
4. **Policy-visible approval** — trusted approval event and Temporal Policy, `LOG_ONLY` before `ENFORCE`.

## Later

- Registry catalog/discovery when multiple agents/tools/skills make reuse a real problem.
- A2A Supervisor only when manual specialist selection becomes a measured usability problem.
- Native WAF/rate limits/evaluations/optimization as product hardening, not MVP plumbing.
