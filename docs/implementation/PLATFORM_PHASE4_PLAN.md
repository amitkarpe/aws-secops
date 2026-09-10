# Platform Phase 4 implementation plan

Status: planned — Issue #15 / PR implementation

Authority: Issue #15

Base: `main` after Platform Phase 3 / PR #14

## Goal

Connect the existing exact Security Group remediation path to the durable backlog as one bounded governed remediation-job lifecycle, without adding another AWS mutation capability.

```text
supported provider finding
-> durable remediation job
-> exact preview
-> human decision
-> Policy
-> retained exact Lambda
-> provider verification
-> durable audit/history
```

## Milestones

### M1 — Supported finding to remediation job

Create one server-owned remediation job only from an existing `REMEDIATION_SUPPORTED` provider-backed Security Group finding. Keep imported CloudSCAPE/VAPT and AWS Config findings PLAN_ONLY. Job identity, finding identity, environment and exact action remain server-owned.

### M2 — Exact preview and human decision

Expose the smallest same-origin API/UI needed to show the exact pending action and permit Reject or Approve DEV. Do not accept arbitrary tools, resources, accounts, Regions or action parameters from the browser/model.

### M3 — Reuse retained governed execution path

Preserve the existing human approval -> Gateway -> Policy -> exact `remove_unrestricted_ssh` Lambda -> provider re-read chain. Preserve Reject and synthetic PROD DENY no-call semantics. Add no new Lambda, Gateway tool, IAM or mutation surface.

### M4 — Durable remediation audit/history

Persist bounded job state/results locally with useful timestamps, decisions, Policy result, provider before/after state and changed flag. Restart must retain history but never replay a mutation automatically. A mitigation plan is not an approval.

### M5 — Proportional end-to-end proof

Using only the existing dedicated personal-lab demo Security Group, prove exact job creation, preview, Reject/DENY no-call behavior, DEV ALLOW exact action, provider COMPLIANT readback and durable audit across restart. Restore the dedicated demo SG to the expected demonstration state afterward.

## Boundaries

- Personal standalone AWS lab only; `ap-southeast-1`.
- Existing exact Security Group remediation only; no second mutation action.
- No new AWS resources, IAM, Gateway tools, service configuration or generic AWS write surface.
- No company/production/GovTech access, multi-account onboarding, Inspector/Security Hub work, LibreChat integration, Supervisor/A2A, Registry, Temporal Policy, EKS, database/workflow framework or automatic mutation retry.
- Never commit account IDs, ARNs, credentials, private endpoints, raw provider evidence or private local state.

## Git / validation economy

Complete M1–M5 as one cohesive 2–3 hour Codex session. Use focused checks during implementation, then one final tests/live-lifecycle/browser-if-useful/diff/public-safety batch and one implementation push by default. Keep corrections in the same PR and return one durable handoff there.