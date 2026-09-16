# Project Status

**Current public baseline:** Demo v1 is frozen and validated. The MkDocs learning portal is live. The separate read-only `aws_secops_operator` AgentCore Harness has been deployed and independently verified. Issue #60 is the current next-phase authority for contextual investigation, a factual agent decision timeline, and a bounded two-account read-only proof.

## What is current

- Personal Singapore lab / POC only.
- Supported remediation families:
  - S3 bucket-level Block Public Access on 100 retained owned empty demo buckets.
  - Restricted SSH on 10 retained owned unattached Security Groups.
- Current Demo v1 interaction path: LibreChat AWS Compliance Agent using native Bedrock Nova 2 Lite with bounded MCP tools.
- Approved Demo v1 execution path: separate human decision per family -> AgentCore Gateway -> Policy -> exact tool -> AWS API -> provider readback.
- AWS Config supplies compliance evidence and converges independently after provider changes.
- Current planners use complete retained-family readiness gates; Demo v1 is not an arbitrary-subset remediation engine.
- The separate `aws_secops_operator` AgentCore Harness is a **read-only** operator path for the two existing Config controls. It has no model-accessible write, shell, generic AWS, or arbitrary resource-selection tool.
- Explicit `fix/apply/execute` requests remain outside the Harness write boundary and route to the existing governed human-approval/executor path.

## Recorded evidence

- PR #23: governed S3 execution, native approval, Gateway/Policy and provider verification.
- PR #25: Config + exact restricted-SSH family and unified-agent direction.
- PR #27: current Config-driven planner, separate S3/SG approvals, repeatable Operator flow and recorded 100-S3 + 10-SG end-to-end acceptance.
- PR #45: read-only AgentCore Harness package for the two existing Config controls.
- PR #50: exact repo/main GitHub OIDC deployment path for the Harness stack.
- PR #53 plus workflow run `34927383714`: GitHub OIDC deployment succeeded from `main`; the exact Harness stack reached `CREATE_COMPLETE`; required CloudFormation outputs were present; Demo v1 mutation was `NO`.
- Issues #49 and #55: independent live Harness/Gateway/Policy/Lambda read verification and negative `fix/apply/execute` boundary completed.
- PR #59: concise operator-summary contract completed with no AWS authority expansion.

See `docs/demo-v1.md` for the Demo v1 evidence digest and exact claim boundaries.

## Issue #60 next-phase implementation

PR #61 adds a bounded agentic workflow without changing the trusted mutation path:

- contextual S3 investigation from existing Config, retained-scope and provider/batch evidence;
- a nine-stage Agent Decision Timeline showing observable evidence/status only, never hidden model chain-of-thought;
- an exactly-two-account **read-only** Config summary implementation with raw account IDs hidden by default;
- a 2–3 minute operator/executive demo path;
- regression tests preserving human approval -> Gateway/Policy -> exact tool -> provider readback.

The two-account implementation is not a live multi-account claim. Runtime proof requires a second explicitly configured owned lab account and independent verification.

## Known limits

- This is not production-ready or arbitrary-resource remediation.
- The two-account feature is read-only and not yet live-proven across two configured owned accounts.
- No cross-account remediation path is implemented or authorized.
- Read-only vs execution intent is partly an agent-behavior rule; hard AWS-change controls remain human approval, Gateway/Policy, exact tools and IAM.
- S3 Operator refresh primarily presents saved durable batch/provider-verification evidence; it should not be described as a fresh full S3 scan on every refresh.
- Issue #32 adds offline-tested S3 and SG safe terminalization plus Config page/token bounds. It does not add automatic continuation, mixed-subset chat retries, or production recovery certification.
- Demo v1 does not claim that a named human identity is itself evaluated by the current Policy decision.
- Demo v1 does not certify complete host-wide least-privilege isolation.
- A Config control finding does not by itself prove sensitive-data exposure, attacker activity, exploitability, or business impact.

## Current work

Issue #60 is current authority. After PR #61 code integration, live activation of the new read-only investigation/timeline tools and the two-account runtime proof are separate authorized verification steps.

Follow `ROADMAP.md` for planned work. Contributors and coding agents use `CONTEXT.md` for compact working continuity.
