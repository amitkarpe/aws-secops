# Phases 8–10 proof — PR #21

Status: connected five-bucket demonstration validated; full-diff review pending.
Evidence date: 2026-09-11. No production-readiness claim.

## M0 decisions

- Verified personal vagent identity privately; explicit ap-southeast-1. Before
  factory: 3 buckets, general-purpose quota 10,000. No Config recorder/rules.
  Account BPA absent; no account-level configuration was changed. Direct S3
  evidence, not AWS Config evaluations, drives this demo.
- Free Tier FREE/ACTIVE observed; estimated net Cost Explorer figure near zero
  is not proof of remaining credits. Live ceiling 10, actual fleet 5. No
  escalation to 50/100/1000. No new compute, Config, logging service or IAM.
- Existing AWS knowledge MCP plus pinned local MCP/Node code selected. No
  Context7 Skill/MCP installed. The decision and official references are in
  the PR M0 comment; no measured token saving is claimed.

## Demonstrated

| Proof | Actual result |
| --- | --- |
| Immutable preview and single-use decision | Focused tests PASS; stale hash/replay rejected |
| Mixed results and crash reconciliation | Tests PASS: SKIPPED/DENIED/COMPLETED, UNKNOWN/read-only reconciliation |
| Single batch writer | Lifetime file lock rejects a second writer |
| 1,000-item offline fixture | PASS; 1,000 verified synthetic items, 20-row page, 1,001-line CSV, durable reopen |
| Offline elapsed time | 49.941 seconds standalone; 63.088 seconds in full suite alongside live work |
| Full deterministic suite | 61 tests PASS, check.sh PASS |
| Live create | Five empty vagent buckets; manifest/tags/owner/Region recorded privately |
| Live safety | ACLs disabled, no policy, no objects/versions/multipart uploads; only BlockPublicAcls false |
| Visible Reject | Playwright PASS: DENIED 5; no apply path invoked |
| Fresh preview + Approve + Run | Playwright PASS: COMPLETED 5, independently re-read BPA all true |
| Export/reload | Five data rows; VERIFIED 5/5 survives browser reload; no JS errors |

Factory reported 91 AWS CLI operations in 85.835 seconds. Ten initial error
counter increments were expected NoSuchBucketPolicy responses, not failed
creation; the counter now excludes that expected absence. Five exact BPA
remediations were verified; the initial live run did not persist aggregate API
metrics. Subsequent saves retain process-scoped metrics without treating them
as billing measurements. No per-item model calls.

## Resource lifecycle and repeatable demonstration

Live reset PASS: 81 API operations / 60.437 seconds, zero API errors and zero
model calls. Separate provider read after reset: five NON_COMPLIANT outcomes,
76 operations / 55.478 seconds, zero API errors. No cleanup performed; the five
buckets remain empty and reset-ready for the next meeting demonstration.

Canonical utility: `scripts/bulk-demo.py create|read|reset|cleanup`.
Private manifest controls exact resources; bucket names/account IDs are not
committed. Factory is create-once. Reset relaxes only BlockPublicAcls and
independently re-reads. Cleanup deletes only verified empty owned buckets and
reads the remaining bucket list; no object deletion code exists.

Reset/cleanup refuse a live writer and unresolved batch states. The resettable
five-bucket fleet is retained for the meeting, owner Amit, phase bulk-bpa,
revision r01, TTL review 18-09-26. TTL does not trigger automatic deletion.
The standalone operator is loopback http://localhost:4444/bulk, with a separate
batch journal; the existing retained amit writer/services were not changed.

Guide: `docs/operations/BULK_S3_DEMO.md`. Four actual Playwright screenshots
(preview/reject/approve/verified) and the meeting copy remain private, outside
Git. Do not publish screenshots containing real bucket identities.

## Connected LibreChat acceptance — 2026-09-11

- Actual named HTTPS LibreChat login, dedicated S3 Compliance Demo agent,
  native Bedrock Nova -> two read-only MCP tools -> five saved NON_COMPLIANT
  findings, recommendation and exact HTTPS batch-review link: PASS.
- Link opened the authenticated named operator page at the same batch ID.
  Unauthenticated access 401; missing/cross-origin/spoofed loopback Origin
  writes 403. Existing operator login and original six reader paths preserved.
- Actual browser Reject -> DENIED 5/no fix dispatch; fresh preview ->
  Approve -> Run -> COMPLETED 5, changed=true for each, four BPA flags true
  after each independent provider read: PASS.
- Same LibreChat conversation called the two batch tools again and displayed
  Count 5, all five updated, Result COMPLIANT, and the latest review link: PASS.
  This is real GUI evidence, not just standalone MCP/API proof.
- Browser reload retained results. Stopped/restarted the exact sole local
  writer; journal SHA-256 unchanged and verified 5/5 after startup: PASS.
- 63 deterministic tests PASS; offline 1,000 items completed in 50.733 seconds
  in the final suite. No browser JavaScript errors in the connected run.
- Dedicated agent's native viewer permission granted only to the unique
  existing Amit user. No public permission or global role change. Amit's
  own browser clicks were not impersonated or claimed as independently tested.
- A standalone non-browser API sharing probe caused LibreChat's expected
  non_browser ban. Exact test-user/IP ban was removed after inspecting its
  native record; global protection remained enabled. Continued with real
  browser login. No replacement account was created to evade the restriction.

Deployment changes: one restricted SSH transport public key on the retained
host; SSH through SSM to EC2 loopback 4444; four exact Nginx bulk routes using
the existing authentication/origin boundary; optional loopback batch MCP origin;
dedicated agent. No AWS credentials copied, new compute, new IAM, DNS or ingress
change. SSM does not log forwarded payloads; the application journal is the
decision/result evidence. WSL uptime is required; no second writer is created.

Private screenshots 05–10 show actual chat findings, HTTPS review/reject/approve,
verified results and chat readback. The connected terminal journal is retained
privately before resetting the fleet for the next demonstration. No real names,
credentials, account IDs or screenshots are committed.

Final ready state: reset five buckets and verified the reset (81 API calls,
0 errors, 58.170 seconds, no model calls). Restarted the sole writer and prepared
a fresh AWS-read preview: five NON_COMPLIANT before settings, PENDING 5,
verified 0, no approval. The connected terminal proof is archived privately.
Nginx, LibreChat and the original backend were active after the final edge check.

## Scope limits and review

- Integrated remote chat -> authenticated operator -> provider -> chat is
  now proven at five live buckets. Never silently switch the runtime identity.
- New batch MCP methods are deployed. No claim of native Gateway enforcement:
  this exact S3 executor uses explicit operator approval and direct CLI.
- No 50/100/1000 live fleet; no account protection/Config service enablement.
- Cleanup implementation is not live-exercised against the retained meeting
  fleet. No batch-wide rollback claim; reset is explicit and demo-only.
- Full PR remains Draft for ChatGPT's actual-diff and evidence review.
