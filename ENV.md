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
- AWS MCP (`M`): primary live AWS discovery/verification path
- GitHub OIDC (`O`): repository-driven short-lived AWS deployment/auth path where defined
- Codex (`X`): optional implementation/runtime worker for cohesive engineering packages
- Python/Bash/CloudFormation: used by existing repo-owned validation/deployment/proof tooling as applicable

## AWS account model

Registered LAB aliases currently used by the multi-account work include:

- `management-lab`
- `personal-lab`

Do not commit raw account IDs or credentials here.

Current multi-account read pattern:

`M-visible hub principal -> sts:AssumeRole -> ChatGPTCrossAccountReadRole`

The IAM path is live-proven. The current AWS MCP runtime does not expose supported dynamic reuse of AssumeRole temporary credentials in later MCP calls; do not claim otherwise.

## Authority

An AWS profile, account alias, GitHub Environment, OIDC role, or MCP connection is not by itself mutation authority. Authority comes from `SPEC.md`, the active Issue/PR, and Amit's current instruction.

## Credentials and secrets

Use approved AWS/GitHub/session mechanisms. Never commit credentials, access keys, tokens, private keys, secret values, or raw session material.
