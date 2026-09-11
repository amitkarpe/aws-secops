# Platform Phases 17–19 plan

Authority: Issue #26
Base: PR #25 merged at `ebdcebb79aa88c6f7af81cbd2ef320004eb32468`
Ownership: ChatGPT implements; Codex deploys/tests the exact implementation.

## Outcome

Turn the retained S3 + Security Group demonstrations into one repeatable, Config-driven operations workflow while simplifying the authenticated Operator homepage:

`Prepare demo -> AWS Config finding -> server-owned plan -> separate native approval -> Gateway/Policy -> exact Lambda -> provider verification -> Config convergence`

Normal remediation stays in **AWS Compliance Agent**. The Operator homepage only prepares/observes exact retained demo resources and never approves remediation.

## Phase 17 — evidence and eligibility

- Fix bounded CloudWatch Logs pagination for isolated Policy DENY=0 / ALLOW=1 proof; review S3 and SG helpers together.
- Keep one server-owned catalog for only the two implemented controls.
- Reconcile Config NON_COMPLIANT evidence with exact retained manifests and direct provider preconditions. Config alone never authorizes a write.

## Phase 18 — Config-driven remediation planning

- Add bounded read-only planning for `all`, S3 BPA, or restricted SSH.
- Explicit fix intent may prepare/freeze one exact server-owned batch from current eligible evidence; caller cannot supply resource IDs, account, Region, API or action.
- Batch preparation is local state only: no AWS remediation and no approval.
- `fix all` plans both families but requests S3 and SG native approvals separately. No cross-family or session-wide approval.

## Phase 19 — repeatable demo + simple Operator homepage

- `https://ops.astromedicomp.org/` becomes a light, two-card Operator homepage for:
  - S3 Block Public Access
  - Security Group restricted SSH
- Each card shows retained resource count, compliant/non-compliant/unknown evidence, latest verification/state evidence, Config status, batch state, View results, Prepare demo, and link to LibreChat.
- Prepare demo requires an exact one-use confirmation, reuses existing provider guards/reset semantics, intentionally restores only the known demo non-compliance, verifies provider state, then creates a fresh PENDING batch.
- Do not show `DEMO READY` unless provider readback and fresh-preview checks both pass.
- Keep `/bulk` and retained audit/history. Preserve authentication and existing URLs; move older operator functionality behind Advanced/Legacy routing during deployment rather than deleting it.
- UI has separate S3 and SG prepare buttons only; no reset-all button.
- Operator-only CLI may support `status`, `reset --s3`, `reset --sg`, and explicit `reset --all`; reset is never exposed through MCP/LibreChat.

## Boundaries

Personal `vagent`, `ap-southeast-1` only. Reuse retained 100 S3 + 10 SG resources. No new fleet, VPC, WAF, Config rule/recorder, generic AWS write tool, screenshots or presentation HTML. SGs remain unattached. S3 remains empty/ACL-disabled/no-policy. Provider verification is remediation truth; Config convergence is asynchronous evidence.

## Acceptance

PASS when Codex deploys this exact PR and proves: bounded log pagination; Config-driven plan; no-ASK read-only behavior; separate S3/SG approval families; provider verification + Config convergence; authenticated Operator homepage with confirmation/cancel and exact prepare behavior; `/bulk` preserved; and no reset capability exposed to the agent.
