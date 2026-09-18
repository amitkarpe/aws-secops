# Environment

Status: READY

Record only project-specific runtime and cloud/tool facts here. Machine-specific host details belong in the active host profile when available.

## Runtime

- Repository: `amitkarpe/aws-secops`
- Runtime: mixed ChatGPT Web + GitHub + AWS MCP + optional local Codex/CLI
- Primary AWS Region: `ap-southeast-1`
- Context: PERSONAL
- Environment: LAB / DEV

## Development tools

- GitHub connector: required for durable Issue/PR/repository control
- AWS MCP (`M`): primary live AWS discovery/verification and, when explicitly authorized, bounded execution path
- GitHub OIDC (`O`): repository-driven short-lived AWS deployment/auth path where defined
- Codex (`X`): fallback implementation/runtime worker for local-only or workspace-heavy tasks that G cannot safely complete through connectors
- Python/Bash/CloudFormation: used by existing repo-owned validation/deployment/proof tooling as applicable

## AWS account model

Registered LAB aliases currently used by the multi-account work include:

- `management-lab`
- `personal-lab`
- `lab-dev`
- `lab-poc`
- `lab-qa`
- `lab-uat`
- `lab-prod`
- `lab-sec`

Do not commit raw account IDs or credentials here.

Multiple AWS MCP account connections may be attached to ChatGPT at the same time.

Operating rule:

`select exact MCP connection -> STS GetCallerIdentity -> verify expected account/Region -> perform bounded work -> independently verify`

Prefer a direct MCP connection for the required account when available. This avoids unnecessary role-chaining and makes account selection explicit. Never persist MCP link IDs, browser session identifiers, OAuth material, or temporary credentials in Git.

Supported multi-account patterns:

1. Preferred when available: `direct AWS MCP account connection -> STS verify -> AWS API`.
2. Existing cross-account read path: `M-visible hub principal -> sts:AssumeRole -> ChatGPTCrossAccountReadRole`.

The IAM AssumeRole path remains live-proven, but do not use it merely out of habit when an explicitly connected account already provides the intended principal. The current AWS MCP runtime does not expose supported dynamic reuse of AssumeRole temporary credentials in later MCP calls; do not claim otherwise.

## Authority

An AWS profile, account alias, GitHub Environment, OIDC role, or MCP connection is not by itself mutation authority. Authority comes from `SPEC.md`, the active Issue/PR, and Amit's current instruction.

## Credentials and secrets

Use approved AWS/GitHub/session mechanisms. Never commit credentials, access keys, tokens, private keys, secret values, or raw session material.
