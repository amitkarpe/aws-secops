# Roadmap

## Completed baseline

- Four-account / two-control Compliance Agent v1.
- Native Approve/Reject boundary with exact frozen scope.
- Selective 1–4 LAB account remediation.
- One-time exact exclusions and timeout/reconciliation hardening.
- Separate AWS service verification and AWS Config evaluation.
- Rich native MCP cards with responsive width/height behavior.
- Authenticated LibreChat API E2E for S3 and SSH Reject-only paths.
- Manual browser Approve/Submit path exercised.
- Single next-action rendering in the native rich card.

## Active — Issue #170

### M0 — Compliance Agent v1 complete

- Release: [`compliance-agent-v1.0.0`](https://github.com/amitkarpe/aws-secops/releases/tag/compliance-agent-v1.0.0)
- Exact release commit: `5d4121eb7e3621d04ae2e05c3b66fdd89879b7e0`
- S3, SSH, and exact-exclusion authenticated Reject-only gates: PASS.
- Automated Approve decisions: zero.
- Issues #141 and #125: closed.

### M1 — sanitized private capability adapter — NOT STARTED

- consume generic control/resource capability metadata from the private catalog;
- support explicit DETECT / EXPLAIN / PREPARE / REMEDIATE / VERIFY states;
- keep unsupported remediation read-only;
- publish no private catalog/account details.

### M2 — scalable query/export, 1K first

- 50 logical accounts;
- 1,000 deterministic synthetic findings;
- server-side filter/sort/search/page;
- capped page size;
- CSV export from backend truth;
- summaries/pages only in model context.

### M3 — bounded bulk Ops pilots

- Agent GUI CSV candidate-scope pilot;
- Config GUI grouped/manual selection pilot;
- exact frozen scope;
- native approval;
- no wildcard approve-all.

### M4 — governed expansion + exceptions/audit

- a few reviewed remediable controls per batch;
- deterministic exclusions/exceptions;
- owner/reason/reference/expiry;
- structured discovery/approval/execution/verification ledger.

### M5 — optional 2K gate

Run only after 1K is green and a real need exists.

**10K/100K are not active scope.**

## Order

`M0 complete -> M1 catalog adapter -> M2 1K query/export -> M3 bulk Ops -> M4 governed expansion -> optional M5 2K`

## Boundaries

- no private policy/catalog details in this public repo;
- no generic model-accessible AWS mutation;
- no CSV-direct execution;
- no silent scope widening/shrinking;
- no session-wide approval;
- no company/PROD rollout;
- each implementation milestone gets its own bounded Issue/PR and E2E gate.
