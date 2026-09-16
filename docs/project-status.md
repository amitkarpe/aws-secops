# Project status

The [root PROJECT_STATUS.md](https://github.com/amitkarpe/aws-secops/blob/main/PROJECT_STATUS.md) is the public source of truth.

Current baseline:

- Demo v1 governed remediation remains the recorded mutation proof.
- The `aws_secops_operator` AgentCore Harness is live and read-only.
- Issue #60 Milestones 1–2 — contextual S3 investigation and the nine-stage Agent Decision Timeline — are live-deployed and healthy-path accepted.
- Config-health failure was verified to fail closed as `UNVERIFIED/BLOCKED`.
- Config-only `CLEAR` is explicitly `provider_state=NOT_READ` / `risk_context=NOT_ASSESSED`.
- Milestone 3 is blocked until a second explicitly authorized owned AWS read scope exists.
- Milestone 4 is consolidating the short demo and public documentation.

For current details, continue with:

- [3-minute demo](operations/AGENTIC_DEMO_3_MIN.md)
- [Architecture](architecture.md)
- [Governance](governance.md)
- [Long Demo v1](demo-v1.md)
- [Roadmap](roadmap.md)
