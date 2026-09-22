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

## Native E2E stop gate

The existing authenticated LibreChat E2E harness remains the required native
card/resume test. This workstation has no retained-runtime private state,
host/tunnel target, running loopback backend, or short-lived E2E bearer token;
therefore an authenticated native `s3_ssl` card and real resume/Reject could
not be run or truthfully represented as passed. No token was created, no
conversation data was created, and no AWS resource was changed.

The remaining acceptance work is to run the existing authenticated harness
against the retained personal-LAB runtime after the runtime connection is
available, extend its fixed scenario to `s3_ssl` (not a generic AWS tool), and
record the real native card/resume/audit cleanup evidence. Until then PR #192
must remain draft and Issue #191 remains open.
