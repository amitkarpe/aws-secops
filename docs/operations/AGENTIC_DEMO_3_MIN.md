# Agentic SecOps — 3-minute multi-account demo

Authority: Issues #82, #88, #87  
Runtime status: **LIVE-ACCEPTED on 2026-09-18**

Management view: [Management audit view](MANAGEMENT_AUDIT_VIEW.md)

## Message

The demo story is:\n\n`Config finding -> Compliance Agent v1 explanation -> explicit fix intent -> frozen plan -> human decision -> exact CodeBuild/G/O execution -> provider readback -> Config convergence`

The AgentCore Harness remains tool-free. **Compliance Agent v1** can invoke only the exact four-account prepare/executor pair; native Approve/Reject authorizes execution.

## 3-minute flow

### 0:00–0:35 — Four-account overview

Ask:

> Show the SecOps overview for lab-dev, lab-poc, lab-qa and lab-sec. Keep identifiers hidden.

Show only the two implemented controls:

- S3 bucket-level Block Public Access
- Security Group restricted SSH

Start from the deliberately prepared demo state: both controls are **NON_COMPLIANT across all four aliases**.

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

Expected result: **zero AWS writes** and Config remains **NON_COMPLIANT x4**.

Then explicitly dispatch:

`S3 + Approve + exact frozen batch id`

Expected execution:

- exactly four bucket-level BPA updates through the tagged OIDC admin session;
- all four BPA settings become TRUE;
- direct S3 readback verifies all four aliases;
- Config may briefly show `PENDING`, then converges to **COMPLIANT x4**.

### 1:30–2:00 — Security Group frozen batch

Prepare/re-arm one **tagged unattached demo Security Group** per alias with exactly one deliberate:

`TCP/22 from 0.0.0.0/0`

Create a separate frozen SG batch covering exactly the same four aliases.

The S3 decision does **not** authorize SG remediation.

### 2:00–2:25 — SG Reject then Approve

First dispatch:

`restricted-ssh + Reject`

Expected result: **zero AWS writes** and Config remains **NON_COMPLIANT x4**.

Then explicitly dispatch:

`restricted-ssh + Approve + exact frozen batch id`

Expected execution:

- exactly four unrestricted SSH rule removals through O;
- every demo SG remains unattached;
- direct EC2 readback proves no TCP/22 ingress from `0.0.0.0/0`;
- Config may briefly show `PENDING`, then converges to **COMPLIANT x4**.

### 2:25–2:50 — Decision Timeline / audit

Show one alias-only timeline:

`Finding -> Investigation -> Recommendation -> Human Decision -> Exact Tool -> Provider Readback -> Config Result`

Important interpretation:

- Reject = `Exact Tool: NOT_CALLED`;
- provider readback = remediation truth;
- Config lag after successful provider readback = `PENDING`, not remediation failure;
- final live acceptance = Config **COMPLIANT x4** for both controls;
- raw account IDs, ARNs, bucket names and SG IDs stay hidden by default.

For the management-ready evidence summary, open the [Management audit view](MANAGEMENT_AUDIT_VIEW.md).

### 2:50–3:00 — Trust close

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

Completed through the G/O path across all four aliases:

1. prepare: safe deliberate non-compliance for both controls;
2. S3 plan: Config **NON_COMPLIANT x4**;
3. S3 Reject: **0 writes**, Config **NON_COMPLIANT x4**;
4. S3 Approve: **4 updates + provider VERIFIED**;
5. S3 Config convergence: **COMPLIANT x4**;
6. SG plan: Config **NON_COMPLIANT x4**;
7. SG Reject: **0 writes**, Config **NON_COMPLIANT x4**;
8. SG Approve: **4 revocations + provider VERIFIED**;
9. SG Config convergence: **COMPLIANT x4**;
10. rerun plans: **ALREADY_COMPLIANT**, 0 writes, provider verified, Config **COMPLIANT x4** for both controls.

## One-line close

> The agent can investigate across accounts, but changes happen only through an explicit control-specific approval, an exact OIDC session, provider verification, and independent Config evidence.


## Recommended screen-recording flow for Compliance Agent v1.0.0

1. Open Config Dashboard and show the four LAB aliases plus both controls.
2. Open LibreChat and select **Compliance Agent v1**.
3. Ask: `Show the current compliance status for all four accounts and both controls.`
4. Ask: `Explain the S3 Block Public Access finding and recommend the fix.`
5. Ask: `Fix S3 Block Public Access across the affected LAB accounts.`
6. Show the native approval card. First choose **Reject** and submit; verify zero dispatch.
7. Ask the S3 fix again. Choose **Approve** and submit; show direct provider verification.
8. Ask: `Fix restricted SSH across the affected LAB accounts.` Approve separately; show provider verification.
9. Ask: `Show the final compliance status for all four accounts and both controls.`
10. Close with: **The agent detects, explains and prepares the fix. The human approves the exact batch, the bounded executor applies it, and provider evidence verifies the result.**
