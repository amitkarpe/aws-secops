# Context

Status: **Demo v1 frozen and validated. Public-sharing work is active under Issue #28.**

## Current truth

- PR #27 merged as the validated Demo v1 baseline.
- The demo is a **personal Singapore lab**, not company or production infrastructure.
- Supported remediation families are intentionally narrow:
  - **S3 bucket-level Block Public Access** on the retained owned demo fleet;
  - **Security Group restricted SSH** on retained owned **unattached** demo groups.
- The validated demo scope is **100 S3 buckets + 10 Security Groups**.
- AWS Config is the compliance detection source. Config can observe more resources than the remediation scope; only exact owned/eligible resources can become a remediation batch.
- Read-only chat intent may explain, summarize, recommend or plan, but must not call an executor.
- An explicit current `fix/apply/execute` request is required before execution intent is prepared.
- S3 and Security Group execution remain **separate native human approvals**. There is no session-wide or blanket `Approve All` authorization.
- Approved writes are routed through **AgentCore Gateway + Policy** to exact bounded remediation tools. The model does not receive a generic AWS mutation tool.
- Direct AWS provider readback is immediate remediation truth. AWS Config convergence is independent and asynchronous.
- Durable batch state reports terminal and uncertain outcomes honestly; `UNKNOWN` is reconciled by readback rather than blind replay.
- The current Operator UI is useful for demo preparation, status and troubleshooting. Raw `/bulk`/batch details are engineering-level views, not the intended long-term operator experience.
- AWS Config, CloudTrail, CloudWatch and direct provider state remain authoritative evidence sources; a future Operations Console should correlate them rather than replace them.
- Public repository content must remain sanitized: no credentials, account IDs, private ARNs/endpoints, auth data, session IDs, raw private findings or private screenshots.

## Demo v1 acceptance already proven

- read-only compliance requests produce no approval and no AWS mutation;
- off-topic requests are rejected by the specialist agent with zero tool use;
- `Fix all` can prepare both supported families while retaining separate native approvals;
- Reject means no dispatch for that exact request;
- Gateway/Policy/exact-tool execution is bounded to the approved server-owned scope;
- provider verification is required for completion;
- the retained 100-S3 and 10-SG demo has been exercised end to end;
- Operator status remains useful when AWS Config is temporarily unavailable;
- AWS Config recorder/delivery health was restored and independently verified.

## Current milestone

Issue #28: **Public repository + MkDocs learning portal**.

Goals:

1. make README / CONTEXT / SPEC human-readable and current;
2. publish curated existing `docs/*.md` through MkDocs Material + GitHub Pages;
3. keep historical phase plans/proofs as deep-dive evidence rather than the public front door;
4. make no runtime or AWS changes for the documentation milestone.

## Next action

Finish the docs-only publication PR, prove `mkdocs build --strict`, publish Pages, and share the repository with technical reviewers. Reviewer questions should drive the next engineering milestone.

Historical implementation detail remains available under `docs/implementation/`, `docs/operations/` and `docs/research/`.
