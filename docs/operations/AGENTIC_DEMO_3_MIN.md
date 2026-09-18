# Agentic SecOps — 3-minute multi-account demo

Authority: Issue #82  
Runtime status: **LIVE-ACCEPTED on 2026-09-18**

Management view: [Management audit view](MANAGEMENT_AUDIT_VIEW.md)

## Message

The demo story is now:

`Config finding -> bounded investigation -> frozen plan -> human decision -> exact OIDC execution -> provider readback -> Config convergence`

The live Harness remains read-only. **O = GitHub OIDC** is the governed mutation path.

## 3-minute flow

### 0:00–0:35 — Four-account overview

Ask:

> Show the SecOps overview for lab-dev, lab-poc, lab-qa and lab-sec. Keep identifiers hidden.

Show only the two implemented controls:

- S3 bucket-level Block Public Access
- Security Group restricted SSH

AWS Config may show `NON_COMPLIANT`, `COMPLIANT`, `PENDING`, or `UNAVAILABLE`. Config is evidence, not execution authority.

### 0:35–1:05 — S3 frozen batch

Prepare/re-arm one **empty tagged demo bucket** per alias through the operator-only OIDC preparation path.

Safety facts:

- no objects;
- no public bucket policy;
- no public ACL;
- no website hosting;
- bucket-level BPA is the only deliberate S3 non-compliance.

Create one frozen S3 batch covering exactly the four aliases. Display the batch id and aliases only.

### 1:05–1:30 — S3 Reject then Approve

First dispatch:

`S3 + Reject`

Expected result: **zero AWS writes**.

Then explicitly dispatch:

`S3 + Approve + exact frozen batch id`

Expected execution:

- exactly four bucket-level BPA updates through the tagged OIDC admin session;
- all four BPA settings become TRUE;
- direct S3 readback verifies all four aliases.

Config convergence is displayed separately and may remain `PENDING`.

### 1:30–2:00 — Security Group frozen batch

Prepare/re-arm one **tagged unattached demo Security Group** per alias with exactly one deliberate:

`TCP/22 from 0.0.0.0/0`

Create a separate frozen SG batch covering exactly the same four aliases.

The S3 decision does **not** authorize SG remediation.

### 2:00–2:25 — SG Reject then Approve

First dispatch:

`restricted-ssh + Reject`

Expected result: **zero AWS writes**.

Then explicitly dispatch:

`restricted-ssh + Approve + exact frozen batch id`

Expected execution:

- exactly four unrestricted SSH rule removals through O;
- every demo SG remains unattached;
- direct EC2 readback proves no TCP/22 ingress from `0.0.0.0/0`.

Again, Config convergence is a separate asynchronous signal.

### 2:25–2:50 — Decision Timeline / audit

Show one alias-only timeline:

`Finding -> Investigation -> Recommendation -> Human Decision -> Exact Tool -> Provider Readback -> Config Result`

Important interpretation:

- Reject = `Exact Tool: NOT_CALLED`;
- provider readback = remediation truth;
- Config lag after successful provider readback = `PENDING`, not remediation failure;
- raw account IDs, ARNs, bucket names and SG IDs stay hidden by default.

For the management-ready evidence summary, open the [Management audit view](MANAGEMENT_AUDIT_VIEW.md).

### 2:50–3:00 — Trust close

Close with:

```text
Read-only agent / M
        |
        v
Evidence + recommendation
        |
        v
Explicit S3 or SG decision
        |
        v
O = GitHub OIDC tagged-admin session
        |
        v
Exact bounded AWS action
        |
        v
Direct provider readback
        |
        v
AWS Config convergence
```

## Live acceptance

Completed through the G/O path:

1. prepare: PASS for all four aliases;
2. S3 frozen batch: PASS;
3. S3 Reject: 0 writes;
4. S3 Approve: 4 updates + provider readback VERIFIED;
5. SG frozen batch: PASS;
6. SG Reject: 0 writes;
7. SG Approve: 4 revocations + provider readback VERIFIED;
8. rerun plans: ALREADY_COMPLIANT for both controls;
9. Config: UNAVAILABLE on all four aliases for both controls, reported separately and never treated as provider failure.

## One-line close

> The agent can investigate across accounts, but changes happen only through an explicit control-specific approval, an exact OIDC session, and provider verification.
