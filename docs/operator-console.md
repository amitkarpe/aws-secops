# Operations Console direction

The Operator page is the management-facing entry point for the four-account SecOps demo.

## Issue #106 / PR #107

This is a **presentation / GUI milestone only**. The existing backend, authentication, approvals and AWS mutation boundary are unchanged.

Before continuing, validate GitHub access and read `AGENTS.md`, `CONTEXT.md`, `SPEC.md` and the owning Issue/PR. Validate AWS MCP with STS against the personal-LAB account specified in Issue #106, using `ap-southeast-1`. Stop AWS work if identity differs or authentication fails. Initial validation is read-only.

## Primary view

The page puts management summary cards and the live risk matrix first:

- exactly `lab-dev`, `lab-poc`, `lab-qa`, `lab-sec`;
- exactly S3 Block Public Access and restricted SSH;
- eight account/control checks, not eight resources;
- **Attention** when any known check is non-compliant, including mixed unknown states;
- **Pending** when evidence is unavailable or only compliant/unknown checks remain;
- **Ready** only when all eight Config checks are compliant. This does not mean a remediation batch is eligible or approved.

Unknown, insufficient-data and not-applicable checks are never counted as compliant. Unexpected aliases, duplicate aliases, the wrong scope/Region, or unavailable/partial responses do not produce a successful live view. Rendering uses fixed aliases and allowlisted states, not raw identifiers or API-supplied HTML.

## Refresh and evidence age

`Refresh live evidence` uses the existing read-only `/api/operator/status` endpoint. It does not prepare or execute remediation. Only one refresh is in flight; failure clears the primary success state and enables retry. The timer updates a local age label, not the backend.

The age shown is **time since the browser received a valid Config response**. It is not AWS Config evaluation age, recorder health, or provider-verification freshness. The existing API does not provide Config evaluation timestamps. The previous successful receipt time remains visible after failure, explicitly alongside unavailable current evidence.

## Execution flow and historical evidence

The explanatory flow is:

`Detect -> Plan -> Human Approval -> Bounded Fix -> Verify`

The existing four-account architecture remains:

`Config -> read-only plan -> frozen exact batch -> native Approve/Reject -> fixed CodeBuild/CodeConnections -> existing G/O controller -> provider readback -> independent Config convergence`

The evidence cards display the existing backend `acceptance` record. That record is saved four-account GitHub OIDC acceptance proof, not a new live execution feed or a timestamped audit log. Counts, provider verification and Config convergence are displayed separately for S3 and SSH. Missing or incomplete records never produce an unconditional success sequence.

Issue #100 and PR #105 contain the later chat/CodeBuild acceptance narrative. In Issue #100's recorded test, Reject was simulated by withholding executor invocation after ASK; this is not a claim that a browser Reject click was exercised by this GUI milestone. PR #107 does not change that backend record or manufacture newer audit events.

Historical Config `COMPLIANT x4` can coexist with current non-compliance after an intentional LAB reset. Only the primary matrix describes the fetched current Config view. No reset or remediation is performed by these UI tests.

## Legacy retained demo

The retained 100-S3 / 10-SG controls and advanced `/bulk` history are inside the collapsed **Legacy retained single-account demo** section. Their existing per-family preview, explicit confirmation and prepare behavior remain unchanged. They do not prepare the primary four-account scope.

## Validation and rollout

The existing offline checks include a credential-free test executing the actual inline JavaScript with Node's built-in VM. It covers primary states, failed refresh/recovery, alias/state validation, absent/incomplete historical evidence and the read-only refresh route. No new framework or package is required.

Synthetic Chromium checks cover desktop, 390px and 320px layouts and legacy cancellation. Synthetic previews are not live AWS verification. Deployment and authenticated live verification remain separate evidence recorded on PR #107 / Issue #106.

## Guardrails

No new AWS control, mutation API, generic administration surface, IAM/SCP change or Config auto-remediation. Preserve Basic Auth and current access controls. S3 and SSH remain separate approvals. Direct provider readback remains remediation truth; Config remains asynchronous independent evidence. Personal LAB only; public/default output remains alias-only.
