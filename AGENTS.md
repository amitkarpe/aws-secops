# AGENTS.md

## Read Order

1. `AGENTS.md`
2. `CONTEXT.md`
3. `SPEC.md`
4. `docs/ARCHITECTURE.md` when architecture/AWS behavior changes.

## Core Rules

- Follow KISS: one useful milestone, one happy path, proportional proof.
- Preserve existing work; do not revert unrelated changes.
- Keep durable code/decisions in Git. Never commit credentials, tokens, session data, private keys, private endpoints, personal/company account IDs/ARNs, or raw private evidence.
- This repository is public. Real non-secret AWS identifiers may appear in the private runtime/demo, but environment-specific identifiers stay outside committed source.
- Update `CONTEXT.md` when current truth or next action changes.
- An approved Issue/SPEC authorizes the normal narrowly scoped AWS/IAM/configuration/deployment/restart/validation work required for that milestone. Stop only on a real safety/scope/identity/account/Region/external-impact expansion.

## AWS / AgentCore

- Live control plane target: `ap-southeast-1`.
- Product workloads run in an approved Organizations member dev/sandbox or security-tooling account, **not** the Organizations management account.
- Never use a company/production account unless a later milestone explicitly authorizes it.
- Development/bootstrap may use interactive AWS access; deployed workloads use workload IAM and cross-account STS where required.
- Actual read/remediation tools must sit behind MCP AgentCore Gateway + Policy. Do not create a generic AWS write shell/API tool.
- Account, Region, role and allowed-action routing are server-owned/allowlisted, not model-selected.
- Prefer provider truth and provider re-read over custom scanners or inferred state.

## AWS CLI First

- For simple AWS reads, setup, verification, or one-off changes, use direct AWS CLI first.
- Prefer `--query`, `--output`, shell variables and command substitution; use `jq` only when needed.
- Do not add Python/SDK/shell wrappers around a few simple CLI commands.
- Application/IaC code is appropriate for reusable runtime behavior, exact tools, policies, tests and non-trivial processing.

## Validation

- Use focused tests for changed behavior.
- Prove live claims proportionally; do not add a new framework merely to collect evidence.
- Report provider evidence and the ALLOW/DENY/mutation result without committing private environment values.

## Global Guidance

When available, use `~/.agent/CORE.md` as shared machine-wide guidance. Agent OS is reusable guidance, never automatic project authority; this repository and its approved Issues/SPECs are authoritative.
