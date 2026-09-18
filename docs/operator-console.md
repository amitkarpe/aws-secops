# Operations Console direction

The Operator page is the management-facing entry point for the **live four-account SecOps demo**.

## Active milestone — Issue #106

Improve `ops.astromedicomp.org` so a manager can understand current risk, approval state and accepted execution evidence in **under 30 seconds**.

This is a **presentation / GUI milestone only**. Do not widen the accepted AWS mutation boundary.

### New ChatGPT session bootstrap

Before implementation, G must:

1. Validate the GitHub app/plugin can read `amitkarpe/aws-secops`.
2. Read `AGENTS.md`, `CONTEXT.md`, `SPEC.md`, Issue #106 and its linked PR.
3. Validate AWS MCP with STS.
4. Continue AWS work only when Account = **`333438771545`** and Region = `ap-southeast-1`.
5. If AWS MCP is disconnected or returns another account, stop AWS work and ask Amit to reconnect the correct MCP session.
6. Keep initial validation read-only.

## Current product truth

Primary scope:

- exactly `lab-dev`, `lab-poc`, `lab-qa`, `lab-sec`;
- S3 bucket-level Block Public Access;
- restricted SSH;
- aliases only — raw account/resource identifiers hidden.

Accepted four-account execution path:

`Config -> read-only plan -> frozen exact batch -> native Approve/Reject -> fixed CodeBuild project -> GitHub App + AWS CodeConnections -> existing G/O controller -> provider readback -> Config convergence`

Live acceptance already proved:

- S3 Reject = zero execution dispatch;
- S3 Approve = four provider-verified changes;
- SG Reject = zero execution dispatch;
- SG Approve = four provider-verified changes;
- Config convergence = `COMPLIANT x4` for both controls;
- compliant rerun fails closed / no new execution.

The LAB demo is intentionally reset to `NON_COMPLIANT x4` for both controls for the next live browser demonstration.

## Management GUI target

The primary Operator Center should emphasize:

- overall demo state: **Ready / Attention / Pending**;
- four-account × two-control live compliance matrix;
- current compliant / non-compliant totals;
- simple flow: **Detect -> Plan -> Human Approval -> Bounded Fix -> Verify**;
- latest accepted execution evidence;
- short audit/evidence timeline;
- Config refresh time / evidence age.

Use the existing backend APIs and current HTML/CSS/JS where possible.

Do not introduce a framework unless the current page truly cannot support the design.

## Legacy retained demo

The earlier 100-S3 / 10-SG runtime remains for engineering/history.

It must be visually secondary and clearly labeled:

> **Legacy retained single-account demo**

Its Prepare buttons affect only retained legacy resources. They do **not** prepare the primary four-account scope.

`/bulk` remains advanced legacy S3 batch history.

## Evidence model

| Evidence | Source of truth |
|---|---|
| Current four-account compliance | Organization AWS Config aggregator |
| Current resource state after change | Direct provider readback |
| Human decision | Native LibreChat Approve / Reject |
| Bounded execution | Fixed CodeBuild project + existing G/O controller |
| AWS API activity | CloudTrail |
| Runtime logs | CloudWatch / service logs |
| Legacy retained workflow state | Durable retained batch journal |

Config is asynchronous evidence. Provider readback remains remediation truth.

## Issue #106 KISS scope

Keep one small PR with about 2–3 related tasks:

1. Rework the primary Operator Center layout for management/demo clarity.
2. Add concise live evidence/status cards using existing backend data.
3. Make legacy content secondary and improve desktop/mobile readability.

## Guardrails

- no new AWS control;
- no new mutation API;
- no generic AWS admin surface;
- no raw AWS identifiers in the default/public UI;
- no SCP change;
- no Config auto-remediation;
- preserve current Basic Auth/access controls;
- S3 and SG remain separate approvals;
- provider readback remains remediation truth;
- personal LAB only.
