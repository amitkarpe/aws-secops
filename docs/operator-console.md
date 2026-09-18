# Operations Console direction

The Operator page is now the management-facing entry point for the **live four-account SecOps demo**.

## Current role

Primary view:

- exactly `lab-dev`, `lab-poc`, `lab-qa`, `lab-sec`;
- live AWS Config organization-aggregator evidence;
- S3 Block Public Access;
- restricted SSH;
- aliases only — raw account/resource identifiers hidden.

The page also shows the latest accepted E2E proof:

`NON_COMPLIANT -> Reject/0 writes -> Approve/provider VERIFIED -> Config COMPLIANT -> rerun/0 writes`

## Legacy retained demo

The earlier 100-S3 / 10-SG runtime still exists for engineering/history.

It is now explicitly labeled:

> **Legacy retained single-account demo**

Its Prepare buttons affect only those retained resources. They do **not** prepare the four-account scope.

`/bulk` remains advanced legacy S3 batch history.

## Compliance Agent relationship

`sec.astromedicomp.org` uses the same current four-account scope for generic status and plan questions.

Four-account chat tools are read-only.

A four-account fix remains on the separately governed G/O path:

`GitHub decision -> GitHub OIDC -> exact AWS change -> provider readback -> Config convergence`

The console must not become a generic account/resource/API selector or a generic AWS admin surface.

## Evidence model

| Evidence | Source of truth |
|---|---|
| Current four-account compliance | Organization AWS Config aggregator |
| Current resource state after change | Direct provider readback |
| Four-account execution decision | Durable GitHub workflow |
| AWS API activity | CloudTrail |
| Runtime logs | CloudWatch / service logs |
| Legacy retained workflow state | Durable retained batch journal |

Config is asynchronous evidence. Provider readback remains remediation truth.

## Useful future additions

Keep future console work narrow:

- visible Config convergence age/timestamp;
- correlation ID across GitHub, provider readback and Config;
- recent bounded execution history;
- CloudTrail / CloudWatch evidence links;
- clear `PENDING`, `UNKNOWN`, `FAILED` and `COMPLIANT` states.

Do not add arbitrary-resource mutation controls merely for convenience.
