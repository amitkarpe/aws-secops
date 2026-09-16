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

### Issue #60 — agentic SecOps next phase

Move from simple `finding -> fix` demonstrations toward:

`investigate context -> explain risk -> recommend exact action -> policy/human decision -> bounded execution -> provider verification -> auditable evidence`

Implementation package: PR #61.

Implemented scope:

1. **Contextual Investigation v1** — bounded S3 Config/retained-scope/provider evidence, explicit uncertainty, no resource selector supplied by the model.
2. **Agent Decision Timeline** — factual nine-stage lifecycle; observable evidence only, no hidden chain-of-thought.
3. **Two-account read-only SecOps** — exact two-scope implementation, read AWS operations only, raw account IDs hidden by default. Live proof remains pending explicit second-account configuration.
4. **Short demo** — 2–3 minute operator/executive flow in `docs/operations/AGENTIC_DEMO_3_MIN.md`.

Credential-free regression and documentation CI passed for the implementation package. No AWS deployment, IAM/OIDC/Gateway/Policy expansion or cross-account mutation is included in code integration.

## Next

### Runtime acceptance for Issue #60

After PR #61 is integrated into `main` and live activation is separately authorized:

- activate the new investigation/timeline tools through the existing governed deployment path;
- independently verify that read-only investigation does not invoke mutation;
- record one S3 investigation + timeline using live existing evidence;
- configure exactly two owned lab read scopes before claiming the multi-account proof;
- independently verify account identity/control summaries and zero mutation with AWS Core.

### Reviewer-driven follow-ons

Consider only after Issue #60 runtime evidence exists:

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
