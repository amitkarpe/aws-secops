# Context

Status: MVP-1 active

## Current Truth

- Product/display name: **AWS Copilot**; repository: `aws-secops`.
- Architecture Decision v1 is frozen from the AgentCore R&D research.
- Active milestone: [Issue #1](https://github.com/amitkarpe/aws-secops/issues/1).
- Target live control plane: AgentCore Harness/Gateway/Policy in Singapore.
- Product workload must run in an approved Organizations member dev/sandbox account, not the management account.
- Repository is public; environment-specific AWS identifiers and private evidence are not committed.
- No clean-product AWS runtime has been deployed from this repository yet.

## Next Action

Implement Issue #1 in the single MVP-1 PR: read-only account/access preflight, then the clean Harness -> Gateway/Policy -> exact Lambda tool -> real Security Group -> provider verification path.
