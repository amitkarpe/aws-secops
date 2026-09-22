# Issue #191: live `s3_ssl` Reject-only evidence

This packet records the bounded, public-safe portion of Issue #191. It is not
an acceptance claim for the authenticated LibreChat native-card journey.

## Fixed live collector

`scripts/issue191_live_s3_ssl_reject.py` accepts no account, bucket, role, or
operation input. It uses the personal-LAB `amit` profile only, resolves exactly
`lab-dev`, `lab-poc`, `lab-qa`, and `lab-sec` from Organizations, verifies the
assumed identity for each existing read role, and issues only S3 `ListBuckets`
and `GetBucketPolicy` reads. The selected region is `ap-southeast-1`.

The collector limits each account to 20 buckets, emits aliases and hashed
resource references only, and makes no AWS write or executor call. An account
or alias mismatch fails closed. Provider errors remain `UNAVAILABLE`; an absent
bucket policy is a `NON_COMPLIANT` result for this TLS control.

## Sanitized live run

The repo-owned runner completed with all four expected aliases identity-verified
and `AVAILABLE`. It collected once, froze one `lab-dev` `s3_ssl` candidate,
made a local bounded `REJECT` decision, then collected again. The canonical
provider evidence digest was unchanged:

| Evidence | SHA-256 digest |
| --- | --- |
| provider evidence before and after Reject | `db9d3cd8fba4e52a96fc8b8eedc765d1cd9c5a35646b8fa1e38bee4456ce9808` |
| frozen batch | `df1eaa48a78e8b5804200625f1d6bc5a695c963631f1ecb459a364d55d9d84c7` |
| frozen scope | `c004be7e2a2b2b160847cf3feb4646855011a472fb7aa87a97f6f62129ef6998` |

The local decision result was `REJECTED`, with `remediation_dispatches = 0`,
`aws_writes = 0`, `automated_approve = false`, and audit events
`PREVIEW_FROZEN` then `NATIVE_APPROVAL_DECISION`. No credentials, account IDs,
role ARNs, bucket names, or endpoints are retained here.

## Retained-runtime identity preflight

On 2026-09-23, the `amit` profile on the existing retained host was STS-verified
as the Organizations management identity and its active Organizations mapping
contained all four registered LAB aliases: `lab-dev`, `lab-poc`,
`lab-qa`, and `lab-sec`. Region selection is fixed to `ap-southeast-1`. The
`vagent` profile is present but resolves to a member-account context and its
Organizations lookup fails with `AWSOrganizationsNotInUseException`; it is not
used for this control.

The live operator service previously had no explicit `SECOPS_LAB_PROFILE`
override and therefore selected `vagent` by default. The PR deployment script
now pins the operator's exact service drop-in to `amit` and checks the running
process environment before declaring readiness. No service or AWS resource
was changed during this preflight. The bounded deployment and native browser
Reject journey are still pending.

## Native E2E stop gate

The authenticated LibreChat native card/resume test remains the acceptance
gate. The retained runtime is reachable for bounded SSM inspection, but the
repo-owned Reject-only integration has not yet been deployed and no native
`s3_ssl` card or decision has been created. The next step is to deploy the
reviewed changes, verify the live fixed read and Reject-only surface, then run
the existing authenticated browser/API harness with Reject only. Do not test
Approve. Until that journey, zero-dispatch evidence, fresh unchanged provider
readback, recovery checks, and cleanup are proven, PR #192 remains draft and
Issue #191 remains open.
