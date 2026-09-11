# Platform Phases 17–19 plan

Authority: Issue #26
Base: PR #25 merge `ebdcebb79aa88c6f7af81cbd2ef320004eb32468`
Status: proposed / implementation pending

## Outcome

Make `AWS Compliance Agent` start from current AWS Config evidence, build a server-owned remediation plan, freeze exact family-specific batches, keep S3 and SG approvals separate, execute through the existing Gateway/Policy targets, verify provider state, and observe Config convergence. Add an operator-only repeat-demo reset. No new AWS resource family in this release.

## Phase 17 — evidence hardening and exact eligibility

- M1: fix bounded CloudWatch Logs pagination in SG Policy proof and the equivalent S3 helper if affected; preserve isolated DENY=0 / ALLOW=1 assertions.
- M2: add one deterministic two-control catalog mapping Config control -> resource type -> exact action family -> provider postcondition -> executor.
- M3: reconcile current Config NON_COMPLIANT resources with the retained manifest-owned demo fleet and direct provider precondition. Never accept model-supplied resource IDs.

## Phase 18 — Config-driven remediation planning

- M4: expose one bounded read-only remediation-plan tool with Config count, owned eligible count, exclusions, exact proposed action and provider postcondition.
- M5: prepare/freeze a local immutable batch from current eligible evidence using only an allowlisted control input. No AWS mutation and no implicit approval.
- M6: `fix all` means plan both supported controls but approve/execute S3 and SG separately. Never one cross-family approval or session-wide Approve All.

## Phase 19 — repeatable technical-demo readiness

- M7: one operator-only CLI command provides status and explicit reset for S3, SG or all existing demo resources. Reset remains inaccessible to MCP/LibreChat.
- M8: after reset, provider-readback first, then bounded Config observation; report `CONFIG_READY` or `PENDING_AFTER_BOUND`, then create fresh previews only after safety checks.
- M9: E2E: reset -> Config evidence -> combined plan -> read-only no-ASK -> separate native approvals -> Gateway/Policy -> exact Lambdas -> direct S3/EC2 verification -> Config convergence -> final chat summary.

## Boundaries

Personal `vagent` Singapore lab only. Reuse retained 100 S3 + 10 SG resources; no scale-up required. No WAF/new VPC/new fleet/new Config rule. No generic AWS mutation surface. No model-selected resource IDs, API, action, account or Region. Reset is operator-only. No new operational HTML page or screenshot requirement. Keep Git churn low.

## Ownership

ChatGPT owns code implementation in this PR. Codex performs read-only preflight and, after ChatGPT implementation lands, deployment/live testing only. Codex must report implementation defects rather than redesign or push fixes unless explicitly asked.
