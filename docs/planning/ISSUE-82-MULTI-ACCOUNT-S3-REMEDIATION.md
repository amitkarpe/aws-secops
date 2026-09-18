# Issue #82 — Multi-account S3 + SG + AWS Config E2E

Goal: prove one end-to-end multi-account SecOps demo through the existing O = GitHub OIDC tagged-admin path.

Scope:
- exactly lab-dev, lab-poc, lab-qa, lab-sec;
- AWS Config evidence for the two existing controls only;
- one empty tagged demo S3 bucket + one tagged unattached demo Security Group per account;
- S3 non-compliance: bucket-level Block Public Access not fully enabled, with no objects/public policy/public ACL/website;
- SG non-compliance: one TCP/22 ingress from 0.0.0.0/0 on an unattached demo SG;
- two frozen four-target batches: S3 and SG;
- S3 and SG approvals remain independent;
- Reject = zero writes for that exact batch;
- Approve S3 = exactly four BPA updates through O;
- Approve SG = exactly four restricted-SSH revocations through O;
- direct provider readback is remediation truth;
- AWS Config convergence is a separate evidence signal and may lag;
- alias-only audit/Decision Timeline output;
- M/Harness stay read-only.

AWS Config:
- reuse recorder/delivery/rules when present;
- if missing in one of the four LAB accounts, provision the smallest repo-owned setup for the two existing managed rules;
- Config never authorizes mutation by itself;
- bounded convergence checks must report PENDING/UNVERIFIED rather than fabricate success.

Acceptance is defined in Issue #82.

G owns this PR and implements as much as GitHub + M permit. X is only needed for any remaining fresh OIDC workflow dispatch/live proof that G cannot start directly.
