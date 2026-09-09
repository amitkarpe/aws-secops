# aws-secops

**AWS Copilot** — an AWS security and compliance copilot built on Amazon Bedrock AgentCore for governed, human-approved, provider-verified remediation.

## Start Here

1. Read `AGENTS.md` for repository rules.
2. Read `CONTEXT.md` for current truth and next action.
3. Read `SPEC.md` for the active trusted contract.
4. Read `docs/ARCHITECTURE.md` for Architecture Decision v1.

## Current MVP

[MVP-1](https://github.com/amitkarpe/aws-secops/issues/1) proves one real Security Group lifecycle:

```text
thin approval UI
  -> AgentCore Harness (Singapore)
  -> MCP Gateway + Policy
  -> exact Lambda MCP tool
  -> workload IAM / STS
  -> real AWS Security Group
  -> provider verification + audit
```

The product does not depend on a personal SSO session at runtime, and the model is never the authorization boundary.

## R&D Reference

The earlier experiments remain in [`mytestlab123/AgentCore`](https://github.com/mytestlab123/AgentCore). This repository promotes only the accepted architecture and proven patterns, not the historical POC plumbing.
