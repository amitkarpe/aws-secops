# Agentic SecOps Next Phase

Authority: Issue #60
Status: planning only

## Objective

Move the demo from simple compliance remediation toward a visibly agentic SecOps workflow:

`investigate context -> explain risk -> recommend exact action -> policy/human decision -> bounded execution -> provider verification -> auditable evidence`

This plan takes inspiration from current AWS agent patterns without trying to clone AWS Security Agent or AWS DevOps Agent. The repository remains focused on a small, governed AWS SecOps proof.

## Guardrails

- Preserve Demo v1 as the trusted baseline.
- Preserve human approval -> Gateway/Policy -> exact tool -> provider readback for mutation.
- No generic model-accessible AWS mutation tool.
- No arbitrary resource selection for mutation.
- Multi-account begins read-only.
- No production claim.
- Prefer one useful proof per milestone.

## Milestones

| Milestone | Outcome | First bounded proof |
| --- | --- | --- |
| 1. Contextual Investigation v1 | Agent investigates before recommending remediation | One retained S3 non-compliant resource; bounded Config/provider/policy/tag/recent-change context |
| 2. Agent Decision Timeline | Operator can see the governed agent lifecycle | Finding -> Investigation -> Risk/Context -> Recommendation -> Policy -> Human Decision -> Exact Tool -> Provider Readback -> Compliance Result |
| 3. Two-account read-only SecOps | Small enterprise-scale discovery proof | Exactly two owned lab accounts; findings/read evidence only; no cross-account mutation |
| 4. Short demo + docs consolidation | Explain value in 2–3 minutes | Problem -> investigate -> recommend -> approve -> exact fix -> AWS proof -> audit timeline |

## Milestone 1 — Contextual Investigation v1

Start with the existing S3 Block Public Access family so the milestone adds agentic investigation rather than a new remediation control.

Bounded evidence may include:

- AWS Config control/finding state;
- current Block Public Access/provider state;
- bucket-policy/public-access context where safely available;
- selected non-sensitive tags/context;
- recent relevant change evidence where practical.

The operator result should state what is wrong, why it matters, evidence used, uncertainty, exact recommendation, and whether approval is required.

The investigation itself is read-only. Explicit fix/apply/execute continues through the existing governed path.

## Milestone 2 — Agent Decision Timeline

Create one reusable operator-facing timeline for both read-only and governed-remediation flows.

Minimum stages:

`Finding -> Investigation -> Risk/Context -> Recommendation -> Policy -> Human Decision -> Exact Tool -> Provider Readback -> Compliance Result`

Show concise facts and status. Hide noisy IDs/ARNs by default. Do not expose or fabricate hidden chain-of-thought; display only bounded reasoning summaries and evidence-backed decisions.

## Milestone 3 — Two-account read-only SecOps

Prove that a central operator can distinguish findings from exactly two owned lab accounts.

Requirements:

- explicit account identity in evidence;
- bounded read-only roles/tools;
- no generic cross-account administrator role;
- no cross-account remediation;
- existing single-account Demo v1 mutation path unchanged.

A later separately reviewed milestone may consider one exact cross-account remediation only after this read-only proof is accepted.

## Milestone 4 — Short demo + documentation consolidation

Create a 2–3 minute story:

1. security problem appears;
2. agent investigates context;
3. evidence/risk is explained;
4. policy chooses the correct path;
5. human approves when mutation is required;
6. exact bounded remediation executes;
7. AWS/provider evidence proves the result;
8. Decision Timeline shows the audit trail.

Keep the longer technical demo separately.

Documentation should converge on a few obvious entry points: README, demo, architecture, security model, and evidence. Do not start with a broad refactor; refactor only code made awkward or duplicated by Milestones 1–3.

## Delivery order

1. Contextual Investigation v1
2. Agent Decision Timeline
3. Two-account read-only proof
4. Short demo/documentation consolidation

Milestones 1 and 2 may share one cohesive implementation PR if still small. Milestone 3 should stay independently safety-reviewable even though Issue #60 tracks the whole phase.

## Planning PR boundary

The planning PR for Issue #60 changes documentation/current authority only. It performs no AWS deployment, IAM/OIDC/Gateway/Policy change, or product implementation.
