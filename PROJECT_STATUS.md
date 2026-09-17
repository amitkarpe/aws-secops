# Project Status

**Current public baseline:** Demo v1 governed remediation remains the recorded mutation proof. The separate `aws_secops_operator` AgentCore Harness is live as the read-only investigation/operator layer. Issue #60 is complete. Issue #70 adds bounded recent-change attribution from CloudTrail Event History. The exactly-two-account proof remains deferred in Issue #68 until a second explicitly authorized owned AWS read scope exists.

## What is current

- Personal Singapore lab / POC only.
- Supported remediation families remain:
  - S3 bucket-level Block Public Access on 100 retained owned empty demo buckets.
  - Restricted SSH on 10 retained owned unattached Security Groups.
- The live `aws_secops_operator` AgentCore Harness uses Nova 2 Lite and exactly four bounded read tools.
- Harness Gateway Policy is `ENFORCE`.
- Harness read scope covers the two existing AWS Config controls plus bounded retained-demo S3 provider context and bounded CloudTrail Event History when a current retained-owned S3 finding exists.
- The Harness has no model-accessible S3 write, EC2 write, SSM, shell, generic AWS, arbitrary resource-selection or remediation tool.
- Explicit `fix/apply/execute` requests remain outside the Harness write boundary.
- Recorded Demo v1 mutation remains a separate path: human decision -> Gateway/Policy -> exact tool -> AWS API -> provider readback.
- AWS Config supplies independent asynchronous compliance evidence.

## Issue #60 — completed agentic SecOps phase

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

Milestone 4 — **3-minute demo + public documentation consolidation**: complete and Pages-deployed.

The former Milestone 3 was moved to standalone Issue #68 because its required second-account prerequisite is not currently available.

## Issue #70 — recent-change attribution v1

Completed and live-accepted.

The existing S3 investigation now includes bounded CloudTrail Event History only when a deterministic retained-owned current finding exists.

Boundaries:

- no new Harness tool;
- no model-selected bucket/resource input;
- only Region-bound `cloudtrail:LookupEvents` added to the existing read Lambda role;
- relevant S3 management-event allowlist only;
- at most five newest relevant events;
- output exposes action + observed time only;
- raw username/principal/account/session identity is suppressed by default;
- recorded API history is not presented as proof of actor identity, intent, root cause, exposure or business impact.

When no current bounded finding exists:

- `provider_state=NOT_READ`;
- `risk_context=NOT_ASSESSED`;
- `provider_evidence=null`;
- recent changes are `NOT_EVALUATED`;
- Config-only CLEAR explicitly does not establish current provider state or absence of exposure/risk.

Final live acceptance verified:

- CloudFormation stack `aws-secops-operator-harness`: `UPDATE_COMPLETE`;
- Harness READY, version 6;
- Gateway READY, Policy mode `ENFORCE`;
- exactly four allowed read tools remain;
- live Decision Timeline reports `Risk / Context = NOT_ASSESSED` for Config-only CLEAR;
- live `Fix this S3 compliance issue` request used only the four read tools and invoked no executor;
- Region-aware IAM simulation allows `cloudtrail:LookupEvents` and denies CloudTrail trail creation, S3 BPA write, EC2 ingress write and SSM `SendCommand`;
- final CloudTrail audit found zero S3 BPA/policy/ACL, SG-ingress or SSM mutation events;
- read Lambda produced zero ERROR events during final acceptance.

## Current Harness boundary

Exactly four allowed tools:

1. `get_config_summary`
2. `list_config_findings`
3. `investigate_s3_context`
4. `get_s3_decision_timeline`

The read Lambda remains bounded to Config reads, four retained-prefix S3 read APIs, Region-bound CloudTrail `LookupEvents`, and logs. Gateway/Policy remains the independent exact read-tool governance layer.

## Recorded mutation evidence

- PR #23: governed S3 execution, native approval, Gateway/Policy and provider verification.
- PR #25: Config + exact restricted-SSH family and unified-agent direction.
- PR #27: recorded Config-driven planner, separate S3/SG approvals and 100-S3 + 10-SG end-to-end acceptance.

## Current agentic evidence

- PR #64: Harness-native contextual S3 investigation + Decision Timeline.
- PR #65: unhealthy Config evidence returns structured `UNVERIFIED/BLOCKED` instead of a masked internal error.
- PR #66: Config-only `CLEAR` is explicitly not provider verification.
- PR #71: bounded CloudTrail recent-change attribution.
- PR #72: Config-only CLEAR exposure/risk semantics hardened after live acceptance.
- Issues #60 and #70: durable deployment/acceptance and security-boundary records.

## Issue #76 — active read-only overview

The reusable cross-account read path is live-proven for the explicitly
registered personal LAB targets. Issue #76 adds the public-safe 3-4 account
overview and control drill-down; it does not add cross-account mutation.

The current AWS MCP runtime still has no supported dynamic assumed-role
credential switch. Local short-lived STS proof is therefore recorded
separately, and the MCP UI does not claim account switching.

## Known limits

- Not production-ready or arbitrary-resource remediation.
- No cross-account remediation path is implemented or authorized.
- No generic autonomous AWS administration.
- A Config control finding alone does not prove sensitive-data exposure, attacker activity, exploitability or business impact.
- A Config-only `CLEAR` does not prove provider state or absence of exposure/risk.
- CloudTrail Event History records API activity; it does not prove a human actor's identity or intent.
- Recorded Demo v1 does not claim named-human identity is itself evaluated by the current Policy decision.
- Complete host-wide least-privilege isolation is not claimed.

## Current work

Issues #60 and #70 are complete. Issue #76 is the active read-only
multi-account overview milestone.

For new unblocked work, create a separate standalone Issue from `ROADMAP.md` rather than mixing unrelated scope into #68.

Follow `ROADMAP.md` for planned work. Contributors and coding agents use `CONTEXT.md` for compact working continuity.
