# Roadmap

## Completed

- Demo v1 frozen and validated.
- 100 retained S3 buckets exercised with exact Block Public Access remediation.
- 10 retained unattached Security Groups exercised with exact restricted-SSH remediation.
- Read-only agent behavior, off-topic scope guardrail, separate native approvals, Gateway/Policy enforcement and direct provider verification recorded.
- Repeatable Operator demo flow and AWS Config integration recorded.
- MkDocs Material learning portal published through GitHub Pages.
- Read-only `aws_secops_operator` AgentCore Harness deployed and independently verified for the two existing AWS Config controls.
- Harness operator-summary polish from Issue #58 / PR #59 completed.
- Issue #60 Milestone 1 — bounded S3 contextual investigation — live-deployed and healthy-path accepted.
- Issue #60 Milestone 2 — factual nine-stage Agent Decision Timeline — live-deployed and healthy-path accepted.
- Unhealthy Config evidence verified to fail closed as `UNVERIFIED/BLOCKED`.
- Healthy zero-finding Config path hardened so `CLEAR` cannot be misrepresented as provider verification.

## Now

### Issue #60 — Milestone 4: short demo + documentation consolidation

The public story is being simplified around the verified architecture:

1. **3-minute demo** — Capability + Evidence Discipline + Trust + Auditability.
2. **Architecture** — live read/investigation plane is separate from recorded governed mutation.
3. **Governance** — prompt intent is not authorization; Harness has no write path.
4. **Evidence/status** — distinguish Config evidence, provider readback and unverified/partial states.

The short demo must work even when the current lab is compliant. It should not require manufacturing a finding simply to tell the story.

A live non-compliant S3 contextual-investigation proof is optional proportional acceptance. If a reviewer specifically needs it, re-arm only one retained demo resource through the explicit operator-only path; never expose reset/re-arm to the Harness.

## Blocked

### Issue #60 — Milestone 3: two-account read-only SecOps proof

The milestone remains valid but is currently **blocked on external authorization**, not on implementation ambition.

Read-only discovery found no existing second owned account/read path to reuse:

- no AWS Organizations membership/path;
- no recent reusable cross-account `AssumeRole` activity;
- no suitable existing cross-account SecOps read role in the current account;
- no second-account/session selector in the current AWS Core connection.

Do not create a broad cross-account administration role merely to complete the milestone.

When a second explicitly authorized owned read scope exists, prove only:

- exactly two accounts;
- account-distinguished read evidence;
- existing supported controls where available;
- zero cross-account mutation authority.

Any cross-account remediation is a separate later security decision.

## Next

### Reviewer-driven follow-ons

Consider only after Issue #60 is closed or explicitly descoped:

- one bounded cross-account remediation path, only after the read-only two-account proof;
- a third security/compliance use case justified by real operator value;
- Security Hub / GuardDuty / CloudSCAPE / VAPT ingestion and investigation;
- formal approval/audit reporting;
- deeper AgentCore/Harness portability or runtime work.

### Publication assurance

Before broad promotion:

- complete reachable-history/publication review for accidental sensitive material;
- decide and document repository licensing/reuse intent;
- improve repository About metadata.

## Later

### Operations Console

Evolve the operator experience into a long-term support console for:

- service/agent health;
- investigation and remediation history;
- Decision Timeline evidence;
- failure reconciliation;
- approval/Policy correlation;
- provider verification;
- links to authoritative AWS evidence;
- version/deployment metadata.

The console should aggregate AWS sources of truth, not replace them, and must never become a generic arbitrary-AWS mutation panel.

No 1,000-live-resource milestone is planned for Demo v1.
