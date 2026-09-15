# Project Status

**Current public baseline:** Demo v1 is frozen and validated. The MkDocs learning portal is live. A separate read-only AgentCore Harness operator path has now been deployed through bounded GitHub OIDC and awaits final independent functional verification.

## What is current

- Personal Singapore lab / POC only.
- Supported remediation families:
  - S3 bucket-level Block Public Access on 100 retained owned empty demo buckets.
  - Restricted SSH on 10 retained owned unattached Security Groups.
- Current Demo v1 interaction path: LibreChat AWS Compliance Agent using native Bedrock Nova 2 Lite with bounded MCP tools.
- Approved Demo v1 execution path: separate human decision per family -> AgentCore Gateway -> Policy -> exact tool -> AWS API -> provider readback.
- AWS Config supplies compliance evidence and converges independently after provider changes.
- Current planners use complete retained-family readiness gates; Demo v1 is not an arbitrary-subset remediation engine.
- A separate `aws_secops_operator` AgentCore Harness is deployed as a **read-only** operator path for the two existing Config controls. It has no model-accessible write, shell, generic AWS, or arbitrary resource-selection tool.

## Recorded evidence

- PR #23: governed S3 execution, native approval, Gateway/Policy and provider verification.
- PR #25: Config + exact restricted-SSH family and unified-agent direction.
- PR #27: current Config-driven planner, separate S3/SG approvals, repeatable Operator flow and recorded 100-S3 + 10-SG end-to-end acceptance.
- PR #45: read-only AgentCore Harness package for the two existing Config controls.
- PR #50: exact repo/main GitHub OIDC deployment path for the Harness stack.
- PR #53 plus workflow run `34927383714`: GitHub OIDC deployment succeeded from `main`; the exact Harness stack reached `CREATE_COMPLETE`; required CloudFormation outputs were present; Demo v1 mutation was `NO`.

See `docs/demo-v1.md` for the Demo v1 evidence digest and exact claim boundaries.

## Known limits

- This is not production-ready, multi-account or arbitrary-resource remediation.
- Read-only vs execution intent is partly an agent-behavior rule; hard AWS-change controls remain human approval, Gateway/Policy, exact tools and IAM.
- The new AgentCore Harness is a separate read-only operator surface; explicit fix/apply/execute requests must still route to the existing governed approval/executor path.
- Final independent live verification of Harness/Gateway/Policy/Lambda behavior and the negative write boundary is still pending before Issue #49 can be closed.
- S3 Operator refresh primarily presents saved durable batch/provider-verification evidence; it should not be described as a fresh full S3 scan on every refresh.
- Issue #32 adds offline-tested S3 and SG safe terminalization plus Config page/token bounds. It does not add automatic continuation, mixed-subset chat retries, or production recovery certification.
- Demo v1 does not claim that a named human identity is itself evaluated by the current Policy decision.
- Demo v1 does not certify complete host-wide least-privilege isolation.

## Current work

Issue #49 is the current closeout gate for the read-only AgentCore Harness deployment. GitHub-side deployment is complete; only independent live functional verification and public-safe closeout evidence remain.

Follow `ROADMAP.md` for planned work. Contributors and coding agents use `CONTEXT.md` for compact working continuity.
