# Phases 8–10 proof — PR #21

Status: meeting demo implemented; integrated release not yet complete.
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

## Remaining release gates

- Integrated remote LibreChat batch read/explain -> local vagent approval ->
  remote chat readback is NOT proven. The local bulk UI/provider is proven.
  Never copy vagent credentials onto the amit host or silently change identity.
- New read-only batch MCP methods/template are implemented but not deployed to
  the retained chat server. No claim of native Gateway enforcement for S3:
  this exact S3 executor uses explicit operator approval and direct CLI.
- No 50/100/1000 live fleet; no account protection/Config service enablement.
- Cleanup implementation is not live-exercised against the retained meeting
  fleet. No batch-wide rollback claim; reset is explicit and demo-only.
- Full PR remains Draft pending the remaining integrated acceptance and review.
