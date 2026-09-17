# Multi-account Harness milestone

Authority: Issue #80

## Goal

Expose the already-proven 3–4 account read-only SecOps overview through the live AgentCore Harness/demo experience.

## Implementation slices

1. Reuse the existing public-safe multi-account backend contract; do not create a second account-discovery implementation.
2. Add the smallest practical Harness-facing surface for organization overview plus one account/control drill-down.
3. Preserve explicit `UNAVAILABLE` evidence handling and prohibit CLEAR/PASS inference when Config evidence is absent.
4. Keep all multi-account actions read-only; explicit `fix/apply/execute` requests must not create a cross-account mutation path.
5. Update the short demo/docs around a management-ready multi-account story.

## Acceptance

- exactly 3–4 registered personal LAB scopes;
- aliases only in default/public output; no raw account IDs/ARNs/private identifiers;
- inventory + IAM summary + supported Config state are visible;
- one account/control drill-down is available;
- `UNAVAILABLE` stays honest;
- no cross-account remediation or generic AWS tool is added;
- existing Harness regressions remain green;
- live acceptance proves overview, drill-down, and mutation refusal.

## Handoff

X continues this existing PR and leaves `HANDOFF: CHATGPT`. G reviews and merges.
