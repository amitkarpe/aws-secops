# Roadmap

## Completed

- Demo v1 frozen and validated.
- 100 retained S3 buckets exercised with exact Block Public Access remediation.
- 10 retained unattached Security Groups exercised with exact restricted-SSH remediation.
- Read-only agent behavior, off-topic scope guardrail, separate native approvals, Gateway/Policy enforcement and direct provider verification recorded.
- Repeatable Operator demo flow and AWS Config integration recorded.
- MkDocs Material learning portal published successfully through GitHub Pages.
- Read-only `aws_secops_operator` AgentCore Harness deployed and independently verified for the two existing AWS Config controls.
- Harness operator-summary polish from Issue #58 / PR #59 completed.

## Now

### Issue #60 — next agentic SecOps phase

Move from simple `finding -> fix` demonstrations toward a stronger operator story:

`investigate context -> explain risk -> recommend exact action -> policy/human decision -> bounded execution -> provider verification -> auditable evidence`

Planning details: `docs/planning/AGENTIC_SECOPS_NEXT_PHASE.md`.

Delivery order:

1. Contextual Investigation v1 — start with the existing S3 family and add bounded read-only evidence/context before recommendation.
2. Agent Decision Timeline — reusable evidence-backed lifecycle view from finding through provider/compliance result.
3. Two-account read-only SecOps proof — exactly two owned lab accounts; no cross-account mutation.
4. Short demo + documentation consolidation — 2–3 minute value story plus simplified entry points.

Preserve Demo v1 and the current mutation boundary throughout.

## Next

### Reviewer-driven follow-ons

Consider only after Issue #60 evidence exists:

- one bounded cross-account remediation path;
- a third compliance/security control justified by a real operator use case;
- CloudSCAPE/VAPT or Security Hub/GuardDuty ingestion and triage;
- formal approval/audit reporting;
- deeper AgentCore/Harness portability or runtime work.

### Publication assurance

Before broad promotion:

- complete reachable-history/publication review for accidental sensitive material;
- decide and document repository licensing/reuse intent;
- improve repository About metadata.

## Later

### Operations Console

Evolve the current Operator UI into a long-term support console for health, investigation/remediation history, failure reconciliation, approval/Policy correlation, authoritative AWS evidence links, provider verification, and deployment metadata.

The console should aggregate and correlate AWS sources of truth, not replace them, and must never become a generic arbitrary-AWS mutation panel.

No 1,000-live-resource milestone is planned for Demo v1.
