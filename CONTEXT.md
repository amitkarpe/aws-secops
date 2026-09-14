# Agent Context

This file is retained for coding-agent/session continuity. Human readers should use `README.md`, `PROJECT_STATUS.md`, `SPEC.md` and the MkDocs site.

## Current product truth

- Demo v1 is frozen and validated.
- Personal Singapore lab only; no company or production resources.
- Supported families remain exactly:
  - S3 bucket-level Block Public Access on the retained owned demo fleet;
  - restricted SSH on retained owned unattached Security Groups.
- Current primary agent path is LibreChat + native Bedrock Nova 2 Lite + bounded MCP tools. Historical Harness experiments are not the current primary architecture.
- S3 and SG retain separate native human approvals.
- Approved execution remains Gateway -> Policy -> exact family tool -> provider readback.
- The model has no generic AWS mutation tool and cannot select arbitrary execution targets.
- Current planners require complete retained-family readiness; no arbitrary-subset claim.
- Provider readback is immediate remediation truth; Config is independent asynchronous evidence.
- Operator Prepare demo is separate operator maintenance and is never an agent reset capability.

## Current publication rule

The repository and site are public. Keep credentials, private infrastructure identifiers, auth material, raw private findings and private screenshots out of Git and public discussions.

## Current work rule

Issue #32 is the active bounded code/docs-hardening milestone: Config pagination and recorder checks, safe S3 and SG interruption terminalization, truthful status evidence, and offline PR tests. Existing two-family scope and approval/Gateway/Policy contracts remain fixed.

This issue authorizes implementation and offline validation only. No AWS calls, reset/re-arm, service restart, deployment, IAM/policy changes, or live remediation are authorized. Preserve the existing `fix/review-hardening` branch/work; never overwrite unrelated changes.

For public status and known limitations use `PROJECT_STATUS.md`. For product/security contract use `SPEC.md`. For future work use `ROADMAP.md`.
