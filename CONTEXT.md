# Context

Status: Phase 0A proposal active

## Current Truth

- Product/display name: **AWS Copilot**; repository: `aws-secops`.
- Existing `mytestlab123/AgentCore` work already proves the governance concept with a real Security Group remediation demo.
- Management approval for a clean product pilot is not yet secured; Friday is the near-term proposal/demo target.
- [Issue #1](https://github.com/amitkarpe/aws-secops/issues/1) is now a proposal/architecture milestone, not full product implementation.
- A standalone personal lab selected locally through `vagent` passed read-only Bedrock + AgentCore Gateway + AgentCore Policy preflight in Singapore.
- That standalone account is the preferred isolated technical lab for the next feasibility milestone; its environment identity stays out of this public repo.
- No clean-product runtime has been deployed from this repository.

## Next Action

Finish PR #2 as a concise proposal package: management story, proposed architecture, proven-vs-proposed boundary, technical validation backlog, scale/cost scenarios, and personal-lab -> company non-production -> production path.

Run actual AgentCore/model/cost experiments in the separate follow-on feasibility milestone rather than deploying the full MVP here.
