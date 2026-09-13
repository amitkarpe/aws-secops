# Roadmap

## Completed

- Demo v1 frozen and validated.
- 100 retained S3 buckets exercised with exact Block Public Access remediation.
- 10 retained unattached Security Groups exercised with exact restricted-SSH remediation.
- Read-only agent behavior, off-topic scope guardrail, separate native approvals, Gateway/Policy enforcement and direct provider verification recorded.
- Repeatable Operator demo flow and AWS Config integration recorded.
- MkDocs Material learning portal published successfully through GitHub Pages.

## Now

- Complete public-release cleanup from technical review:
  - make current Demo v1 the unmistakable default reading path;
  - label historical pilot/Harness material clearly;
  - tighten trust-model and evidence wording;
  - improve repository/publication hygiene without changing AWS/runtime scope.
- Share the repository with internal technical reviewers and collect concrete questions.

## Next

### Operator-summary polish

Improve the AWS Compliance Agent default response style for concise operator summaries: Markdown tables, a small consistent emoji vocabulary, and hidden batch/resource IDs unless explicitly requested.

### Bounded reliability hardening

Track separately from documentation work:

- define and test a safe SG continuation/terminalization path for mid-batch interruption scenarios;
- add page/token bounds to AWS Config pagination and targeted fake-client tests;
- add high-value PR checks using the existing offline regression suite where they can run without live AWS credentials.

### Publication assurance

- complete a full reachable-history/publication review for accidental sensitive material before broad social promotion;
- decide and document repository licensing/reuse intent;
- improve repository About metadata.

## Later

### Operations Console

Evolve the current Operator UI and raw `/bulk` engineering view into a long-term admin/support console for:

- platform/service health;
- remediation job history and progress;
- failure/UNKNOWN troubleshooting and reconciliation;
- approval and Policy-result correlation;
- links to authoritative CloudTrail, CloudWatch and AWS Config evidence;
- direct provider-verification status;
- version/deployment metadata and audit correlation IDs.

The console should **aggregate and correlate**, not replace AWS sources of truth. It must never become a generic arbitrary-AWS mutation panel.

### Possible reviewer-driven milestones

- a third compliance control only when justified by a real use case;
- multi-account design;
- CloudSCAPE/VAPT ingestion and triage;
- formal approval/audit reporting;
- deeper AgentCore/Harness portability or runtime work.

No 1,000-live-resource milestone is planned for Demo v1.
