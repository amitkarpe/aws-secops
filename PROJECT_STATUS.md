# Project Status

**Current public baseline:** Demo v1 is frozen and validated. The MkDocs learning portal is live.

## What is current

- Personal Singapore lab / POC only.
- Supported remediation families:
  - S3 bucket-level Block Public Access on 100 retained owned empty demo buckets.
  - Restricted SSH on 10 retained owned unattached Security Groups.
- Current primary interaction path: LibreChat AWS Compliance Agent using native Bedrock Nova 2 Lite with bounded MCP tools.
- Approved execution path: separate human decision per family -> AgentCore Gateway -> Policy -> exact tool -> AWS API -> provider readback.
- AWS Config supplies compliance evidence and converges independently after provider changes.
- Current planners use complete retained-family readiness gates; Demo v1 is not an arbitrary-subset remediation engine.

## Recorded evidence

- PR #23: governed S3 execution, native approval, Gateway/Policy and provider verification.
- PR #25: Config + exact restricted-SSH family and unified-agent direction.
- PR #27: current Config-driven planner, separate S3/SG approvals, repeatable Operator flow and recorded 100-S3 + 10-SG end-to-end acceptance.

See `docs/demo-v1.md` for the evidence digest and exact claim boundaries.

## Known limits

- This is not production-ready, multi-account or arbitrary-resource remediation.
- Read-only vs execution intent is partly an agent-behavior rule; hard AWS-change controls remain human approval, Gateway/Policy, exact tools and IAM.
- S3 Operator refresh primarily presents saved durable batch/provider-verification evidence; it should not be described as a fresh full S3 scan on every refresh.
- Issue #32 adds offline-tested SG safe terminalization and Config page/token bounds. It does not add automatic SG continuation, mixed-subset chat retries, or production recovery certification.
- Demo v1 does not claim that a named human identity is itself evaluated by the current Policy decision.
- Demo v1 does not certify complete host-wide least-privilege isolation.
- Earlier Harness, multi-source pilot and phase-plan material is retained as history/research and is not the current primary architecture.

## Current work

Public-release navigation/claim cleanup is complete (PR #31). [Issue #32](https://github.com/amitkarpe/aws-secops/issues/32) hardens the same two-family code paths and adds repeatable offline PR checks. It does not authorize a live deployment or AWS operation.

The historical live acceptance remains separate from new offline checks. The [hardening evidence](docs/implementation/RELIABILITY_HARDENING_PROOF.md) records the baseline, reproduced defects, recovery semantics, and outstanding deployment validation.

Follow `ROADMAP.md` for planned work. Contributors and coding agents use `CONTEXT.md` for compact working continuity.
