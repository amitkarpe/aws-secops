# Roadmap

## Completed

- Demo v1 frozen and validated.
- 100 retained S3 buckets exercised with exact Block Public Access remediation.
- 10 retained unattached Security Groups exercised with exact restricted-SSH remediation.
- Read-only agent behavior, off-topic scope guardrail, separate native approvals, Gateway/Policy enforcement and direct provider verification proven.
- Repeatable Operator demo flow and AWS Config integration proven.

## Now

- Issue #28: prepare the public repository for technical sharing.
- Publish the existing documentation as a curated MkDocs Material GitHub Pages learning portal.
- Keep Demo v1 runtime frozen while documentation/publication is completed.

## Next

- Improve the AWS Compliance Agent default response style for concise operator summaries: Markdown tables, a small consistent emoji vocabulary, and hidden batch/resource IDs unless explicitly requested.
- Collect feedback from technical reviewers and use their questions to select the next engineering milestone.

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
