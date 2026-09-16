# Project Status

**Current public baseline:** Demo v1 governed remediation remains the recorded mutation proof. The separate `aws_secops_operator` AgentCore Harness is live as the read-only investigation/operator layer. Issue #60 Milestones 1–2 are live-deployed and healthy-path accepted; Milestone 3 is blocked pending a second explicitly authorized owned AWS read scope; Milestone 4 is consolidating the short demo and public documentation.

## What is current

- Personal Singapore lab / POC only.
- Supported remediation families remain:
  - S3 bucket-level Block Public Access on 100 retained owned empty demo buckets.
  - Restricted SSH on 10 retained owned unattached Security Groups.
- The live `aws_secops_operator` AgentCore Harness uses Nova 2 Lite and exactly four bounded read tools.
- Harness Gateway Policy is `ENFORCE`.
- Harness read scope covers the two existing AWS Config controls plus bounded retained-demo S3 provider context when a current Config finding exists.
- The Harness has no model-accessible S3 write, EC2 write, SSM, shell, generic AWS, arbitrary resource-selection or remediation tool.
- Explicit `fix/apply/execute` requests remain outside the Harness write boundary.
- Recorded Demo v1 mutation remains a separate path: human decision -> Gateway/Policy -> exact tool -> AWS API -> provider readback.
- AWS Config supplies independent asynchronous compliance evidence.

## Issue #60 live acceptance

Milestone 1 — **Contextual Investigation v1**: live-deployed and accepted.

- bounded current Config evidence;
- deterministic retained-demo S3 candidate selection when a finding exists;
- direct S3 provider context only within the fixed read scope;
- explicit uncertainty;
- no model-selected bucket input;
- no mutation authority added.

Milestone 2 — **Agent Decision Timeline**: live-deployed and accepted.

- nine observable stages from Finding through Compliance Result;
- evidence/status only, never hidden chain-of-thought;
- governance stages show `NOT_CALLED` / `NOT_REQUESTED` when no mutation path ran.

The live acceptance covered both important evidence states:

1. **Unhealthy Config** — fail closed as `UNVERIFIED/BLOCKED`; no fabricated current result and no mutation.
2. **Healthy Config with zero bounded findings** — Config-only `CLEAR` with `provider_state=NOT_READ`, `risk_context=NOT_ASSESSED`, and no provider-verification claim.

An explicit live fix request through the Harness produced no AWS mutation.

## Current Harness boundary

Exactly four allowed tools:

1. `get_config_summary`
2. `list_config_findings`
3. `investigate_s3_context`
4. `get_s3_decision_timeline`

The read Lambda remains bounded to Config reads, four retained-prefix S3 read APIs, and logs. Gateway/Policy remains the independent exact read-tool governance layer.

## Recorded mutation evidence

- PR #23: governed S3 execution, native approval, Gateway/Policy and provider verification.
- PR #25: Config + exact restricted-SSH family and unified-agent direction.
- PR #27: recorded Config-driven planner, separate S3/SG approvals and 100-S3 + 10-SG end-to-end acceptance.

## Current agentic evidence

- PR #64: Harness-native contextual S3 investigation + Decision Timeline.
- PR #65: unhealthy Config evidence returns structured `UNVERIFIED/BLOCKED` instead of a masked internal error.
- PR #66: Config-only `CLEAR` is explicitly not provider verification.
- Issue #60: durable live deployment/acceptance and security-boundary record.

## Milestone 3 — blocked, not claimed

The exactly-two-account read-only proof is **not live-proven**.

Current read-only discovery found:

- no AWS Organizations membership/path to reuse;
- no recent reusable cross-account `AssumeRole` path;
- no existing local cross-account SecOps read role suitable for reuse;
- no second account/session selector in the current AWS Core connection.

No cross-account role, trust or broad administration capability was created merely to complete the milestone.

Milestone 3 requires a second explicitly authorized owned AWS read scope before any two-account claim is made.

## Milestone 4 — current documentation/demo work

The public story is being consolidated around:

1. [3-minute demo](docs/operations/AGENTIC_DEMO_3_MIN.md)
2. [current architecture](docs/architecture.md)
3. [governance / security model](docs/governance.md)
4. [long Demo v1](docs/demo-v1.md)
5. this current status page

The short demo emphasizes **Capability + Evidence Discipline + Trust + Auditability**. It does not pretend that the read-only Harness can remediate AWS.

## Known limits

- Not production-ready or arbitrary-resource remediation.
- No live multi-account proof yet.
- No cross-account remediation path is implemented or authorized.
- No generic autonomous AWS administration.
- A Config control finding alone does not prove sensitive-data exposure, attacker activity, exploitability or business impact.
- A Config-only `CLEAR` does not prove provider state.
- Recorded Demo v1 does not claim named-human identity is itself evaluated by the current Policy decision.
- Complete host-wide least-privilege isolation is not claimed.

## Current work

Issue #60 remains the current authority. Milestones 1–2 are accepted; Milestone 3 is blocked on external second-account authorization; Milestone 4 is the current documentation/demo milestone.

Follow `ROADMAP.md` for planned work. Contributors and coding agents use `CONTEXT.md` for compact working continuity.
