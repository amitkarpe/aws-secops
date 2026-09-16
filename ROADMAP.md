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
- Issue #60 Milestone 4 — 3-minute demo + public documentation consolidation — merged, Pages-deployed and regression-verified.
- Issue #60 parent phase completed with blocked Milestone 3 replaced by standalone Issue #68.

## Blocked / deferred

### Issue #68 — two-account read-only SecOps proof

This is the former Issue #60 Milestone 3. It remains valid but is blocked on an external prerequisite: a second explicitly authorized owned AWS read scope.

Current verified blocker:

- no AWS Organizations membership/path;
- no recent reusable cross-account `AssumeRole` activity;
- no suitable existing second-account SecOps read role;
- no second-account/session selector in the current AWS Core connection.

Do not create a broad cross-account administration role merely to complete the proof.

When the prerequisite exists, prove only:

- exactly two explicit owned account scopes;
- account-distinguished read evidence;
- minimum identity + existing supported compliance reads;
- zero cross-account mutation authority;
- unchanged single-account governed mutation path.

Any cross-account remediation is a separate later security decision.

## Next

### Reviewer-driven follow-ons

Choose a new standalone Issue only when there is a concrete operator/reviewer need. Candidates:

- one bounded cross-account remediation path, only after Issue #68 succeeds;
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
