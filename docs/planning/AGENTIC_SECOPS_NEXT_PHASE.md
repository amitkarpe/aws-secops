# Agentic SecOps Next Phase

Authority: Issue #60
Status: implementation in PR #61; no live AWS deployment from this PR

## Objective

Move the demo from simple compliance remediation toward a visibly agentic SecOps workflow:

`investigate context -> explain risk -> recommend exact action -> policy/human decision -> bounded execution -> provider verification -> auditable evidence`

The direction is inspired by current AWS Security Agent / DevOps Agent investigation patterns without attempting to clone those products. This repository remains a small, governed AWS SecOps proof.

## Guardrails

- Preserve Demo v1 as the trusted baseline.
- Preserve human approval -> Gateway/Policy -> exact tool -> provider readback for mutation.
- No generic model-accessible AWS mutation tool.
- No arbitrary resource selection for mutation.
- Multi-account begins read-only.
- No production claim.
- Hide resource/account identifiers by default.
- Do not expose or fabricate model chain-of-thought; show evidence-backed summaries and observable decisions only.

## Milestone status

| Milestone | PR #61 implementation | Runtime status |
| --- | --- | --- |
| 1. Contextual Investigation v1 | `pilot_v1/agentic_evidence.py` + `investigate_s3_context` agent tool | Offline/CI proof required; no AWS mutation |
| 2. Agent Decision Timeline | Reusable nine-stage factual timeline via `get_s3_decision_timeline` | Offline/CI proof required; existing live provider evidence can populate it after deployment |
| 3. Two-account read-only SecOps | `pilot_v1/multi_account_read.py`; exactly two explicit scopes, read APIs only, account IDs hidden | Live proof intentionally pending two configured owned lab accounts |
| 4. Short demo + docs | `docs/operations/AGENTIC_DEMO_3_MIN.md` | Ready for review; deployment is separate |

## Milestone 1 — Contextual Investigation v1

The first implementation reuses the existing S3 Block Public Access family rather than adding another remediation control.

The investigation packet is built from existing bounded evidence:

- AWS Config control state;
- intersection with retained owned demo scope;
- direct provider precondition evidence from the current immutable batch when available;
- exact remediation recommendation;
- explicit uncertainty.

The implementation intentionally does **not** infer data sensitivity, actual public data exposure, attacker activity, exploitability, business impact, or intent from a Config finding.

No resource identifier is accepted from the model for this investigation. The backend selects the current server-owned S3 scope/batch evidence.

## Milestone 2 — Agent Decision Timeline

The timeline stages are:

`Finding -> Investigation -> Risk/Context -> Recommendation -> Policy -> Human Decision -> Exact Tool -> Provider Readback -> Compliance Result`

Each stage is derived from observable Config, plan, batch, approval, Policy/executor, or provider state. The timeline explicitly records that chain-of-thought is not collected or displayed.

Important truth rules:

- Policy is `NOT_CALLED` until an exact executor is invoked.
- Native human approval is independent from investigation/recommendation.
- Provider readback is remediation truth.
- `UNKNOWN` is never success or zero change.
- AWS Config is reported separately because convergence can lag.

## Milestone 3 — Two-account read-only SecOps

The implementation requires exactly two explicit account scopes:

- label;
- AWS profile;
- expected account ID;
- fixed Region `ap-southeast-1`.

The read path permits only `get-*`, `list-*`, and `describe-*` AWS CLI operations and currently reads identity plus Config compliance for the two existing controls. Raw account IDs are replaced by a short hash-based reference in returned evidence.

This PR does not create cross-account roles and does not add any cross-account mutation path. Live acceptance is intentionally pending until a second owned lab account is explicitly configured and independently verified.

## Milestone 4 — Short demo

Use `docs/operations/AGENTIC_DEMO_3_MIN.md`.

The three-minute story is:

1. supported finding appears;
2. agent performs bounded contextual investigation;
3. evidence/risk/uncertainty are shown;
4. Decision Timeline makes the state visible;
5. explicit fix request enters the existing native human approval path;
6. exact bounded executor runs only after approval;
7. direct provider readback proves the result;
8. Config convergence remains a separate evidence signal.

The longer technical Demo v1 remains available separately.

## Deployment boundary

PR #61 implements code, tests and documentation only. It does **not**:

- deploy AWS resources;
- change IAM/OIDC roles;
- widen AgentCore Gateway/Policy;
- add a model-accessible AWS write;
- configure a second account;
- claim a live two-account proof.

After merge, live activation must use the existing governed deployment/operations workflow and independent AWS verification. Any cross-account role or cross-account mutation remains a separate security-reviewed decision.
