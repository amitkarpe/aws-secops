# CODEX reset sprint — Issue #173

This file is a short durable pointer. The full execution contract lives in GitHub Issue #173.

## Objective

Use the resumed Codex session for one substantial end-to-end job:

`finish Compliance Agent v1 closure -> publish current v1.0.0 -> leave Issue #170 clean at M1`

Do not start the future catalog/1K/bulk roadmap.

## Work continuously

Codex owns the active Issue #173 PR until acceptance or a real stop gate.

Do not wait for Amit between:

- repo review;
- implementation;
- tests;
- fixing test failures;
- retained-LAB Reject-only validation;
- release workflow creation;
- GitHub Actions validation;
- safe merge;
- release verification;
- context/roadmap cleanup.

## Read first

1. `AGENTS.md`
2. `CONTEXT.md`
3. `SPEC.md`
4. Issue #173
5. Issue #141
6. Issue #125
7. Issue #170
8. active PR for #173

## Key safety

- personal LAB only;
- no company/PROD;
- no automated Approve;
- exception E2E must submit Reject only;
- zero remediation-execution dispatch / zero AWS resource writes after Reject;
- no secrets/private identifiers in commits, logs, comments or release notes;
- no broad IAM/OIDC/network changes;
- no new product architecture;
- reuse existing harnesses and release patterns.

## Expected finish

- Issue #141 closed with explicit Reject evidence;
- current v1 candidate green;
- fresh `compliance-agent-v1.0.0` release published from current validated commit;
- Issue #125 closed;
- `CONTEXT.md` updated to release truth;
- Issue #170 remains open and ready for M1;
- no stale release PR remains.
