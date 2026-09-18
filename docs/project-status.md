# Project status

The [root PROJECT_STATUS.md](https://github.com/amitkarpe/aws-secops/blob/main/PROJECT_STATUS.md) is the public source of truth.

Current baseline:

- exactly four live LAB aliases: `lab-dev`, `lab-poc`, `lab-qa`, `lab-sec`;
- exactly two supported controls: S3 Block Public Access and restricted SSH;
- `ops.astromedicomp.org` shows live organization Config status for all four aliases;
- `sec.astromedicomp.org` defaults generic status and planning to the four-account read-only scope;
- four-account writes remain on the separate governed GitHub OIDC G/O path;
- Reject = zero writes;
- Approve = four exact provider-verified changes per supported control;
- AWS Config converges independently to `COMPLIANT x4`;
- rerun = `ALREADY_COMPLIANT` / zero writes;
- the retained 100-S3 / 10-SG runtime remains only as a clearly labeled legacy single-account demo.

For current details, continue with:

- [3-minute demo](operations/AGENTIC_DEMO_3_MIN.md)
- [Management audit view](operations/MANAGEMENT_AUDIT_VIEW.md)
- [Architecture](architecture.md)
- [Operations Console](operator-console.md)
- [Governance](governance.md)
