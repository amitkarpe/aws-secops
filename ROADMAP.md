# Roadmap

## Completed

- Demo v1 retained-resource S3/SSH governance and provider-verification proof.
- Four-account provider E2E and organization AWS Config evidence.
- Four-account bounded remediation path with separate approval, fixed execution path, provider readback and independent Config convergence.
- Unified Config Dashboard and four-account demo re-arm.
- Legacy 100-S3 / 10-SG Operator path retired from the active product surface.
- Read-only `aws_secops_operator` AgentCore Harness experiments and contextual investigation milestones.
- Issue #68 is closed; its original two-account prerequisite is no longer the current roadmap gate.
- Compliance Agent v1 implemented as a clean isolated AgentCore Harness-backed specialist.
- Compliance Agent v1 live E2E: Config 4×2 checks, five golden prompts, one-tool MCP, LibreChat authenticated smoke, zero mutation.
- Selective 1–4 LAB account remediation with exact frozen scope and native approval — Issue #147.
- Fast remediation response with separate read-only AWS service verification and independent AWS Config evaluation — Issue #147.
- Concise demo prompts, readable status tables and single native Approve/Reject + Submit handoff — Issues #148/#151.
- Four-account demo re-arm restored after selective-scope rollout, including mixed-state idempotency regression — Issue #153.

## Current

### Compliance Agent v1 release closure

- make LibreChat access reproducible rather than relying on one-off ACL repair;
- keep a real stdio MCP initialization regression in CI;
- publish immutable GitHub Release `compliance-agent-v1.0.0`;
- close Issues #123/#125 after release evidence is verified.

### Scalable Ops UX + governed exceptions — Issue #140

Issue #140 is the future master roadmap for:
- rich inline Ops cards;
- CSV/export;
- deterministic one-time exclusions;
- managed exception registry and expiry;
- 50+ account pagination/filter/query contracts;
- Artifact analytics;
- Jira integration;
- exception governance/audit lifecycle;
- large-scale performance acceptance.

Do not implement all of #140 as one change. Choose one bounded milestone at a time.

Active bounded Ops UX milestone: **Issue #155 — native LibreChat MCP rich results**.

Issue #155 implements Phase 1 only:
- fleet compliance status card;
- remediation preview card;
- remediation result / verification card;
- progressive disclosure for batch/scope technical IDs;
- simple Ops wording: AWS change, AWS service verification, AWS Config evaluation.

CSV/export remains the next separate bounded UX milestone after visual acceptance of #155.

First bounded exception milestone: **Issue #141**.

Issue #141 plans exact one-time exclusions for the current two controls only:
- `Fix all S3 findings except bucket X`;
- `Fix restricted SSH except security group Y`.

Required rule:

`discovered_set - excluded_set = included_set`

The approval view must show included and excluded resources before execution. Excluded resources remain truthful AWS findings and are never reported as fixed.

### Read-only AWS MCP evidence source — Issue #130

Evaluate the already-proven persistent read-only AWS MCP for investigation/evidence only:

- Config;
- S3 posture;
- Security Group posture;
- Inspector;
- CloudTrail Event History;
- IAM/resource inventory.

It must not bypass the existing governed mutation path.

## Future direction — Issue #164

Feedback from the latest review adds three long-term product requirements. Issue #164 is the planning authority; each implementation step must still get its own bounded Issue/PR.

### IM8-authoritative control catalog

- Treat the IM8 clause / reform-control mapping as the authoritative policy taxonomy; the LLM must not invent mappings or control semantics.
- Maintain a deterministic versioned registry: IM8 clause/control -> CloudSCAPE AWS rule -> AWS resource type -> evidence source -> support state.
- Track support independently as `DETECT / EXPLAIN / PREPARE / REMEDIATE / VERIFY`.
- Expand in small batches: first 5–10 new read-only controls, then only 2–3 reviewed remediable controls at a time.
- Every mutable control keeps the existing exact-scope, native approval, provider-readback and Config-convergence boundary.

### Bulk operations for Ops teams

Two UX paths must converge on the same governed backend batch contract:

1. **Agent GUI CSV upload** — CSV supplies candidate scope only; backend validates current evidence, deduplicates, reports included/excluded/rejected rows, freezes the exact batch, then requires native approval.
2. **Config GUI group/manual fix** — server-side filter/group/select by IM8/control/account/resource type/status; **Prepare fix** freezes the exact selected scope and uses the same approval/execution path.

CSV content or a GUI selection is never direct mutation authority.

### 1k+ resource / many-control E2E

- Build deterministic synthetic tiers for 1k, 10k and 100k findings across 50+ accounts and an expanding IM8 control catalog.
- Test summary/count integrity, pagination/filter/grouping, CSV validation, exact frozen scope, Reject=zero-write, stale/replay/restart/TTL behavior, partial account/provider failure and export integrity.
- Keep raw fleet data out of model context; use server-side summaries/pages.
- Use synthetic/no-op execution for large-scale Approve-path state-machine tests; retained-LAB automated E2E remains Reject-only unless separately authorized.
- Measure performance first, then set explicit budgets from evidence rather than guessed thresholds.

Recommended order:

`M0 IM8 registry -> M1 5–10 read-only controls -> M2 1k scale/query foundation -> M3 Agent CSV pilot -> M4 Config GUI grouping pilot -> M5 2–3 remediable controls/batch -> M6 10k/100k acceptance`

Issue #140 remains the companion detailed roadmap for rich results, exports, exceptions, pagination and audit lifecycle. Issue #164 adds policy authority, bulk-fix input/selection and larger control/resource E2E.

## Later

- managed/persistent exception registry with owner, reason, approval, expiry/review date and Jira/change reference;
- rich MCP UI resources and CSV export for large Ops result sets;
- 50+ account / 100k-finding scale contracts with server-side pagination/filtering;
- structured operational event ledger for exact agent-mediated change history;
- AgentCore Memory for conversational/episodic continuity, not authoritative audit;
- Bedrock Knowledge Bases/RAG when unstructured runbooks, SOPs, policies and incident narratives justify semantic retrieval;
- broader AWS Ops Agent only after stable specialist contracts are proven;
- additional controls only when justified by operator value and reviewed as separate milestones.

## Publication assurance

Before broader promotion:

- review reachable history for accidental sensitive material;
- decide/document repository licensing and reuse intent;
- improve repository About metadata.

Demo v1 remains the four-account / two-control baseline. Issue #164 scale targets are future synthetic/controlled acceptance tiers, not a requirement to create 1,000 live AWS resources.
