# Integrated release: Phases 5-7

Status: planned; implementation and live acceptance NOT YET performed.

Authority: [Issue #17](https://github.com/amitkarpe/aws-secops/issues/17).
Base: PR #16 merged at `a65347aee76c39afe33d6acfcbaf7db1bd1ce1da`.

## Outcome

LibreChat can query the real AWS SecOps backlog, request a grounded specialist
explanation, inspect remediation history and open the exact existing operator
view for human planning/approval. The backend remains the authority.

```text
LibreChat -> restricted MCP -> existing backend -> durable findings/jobs
                              |
                              +-> zero-tool specialist explanation
                              +-> exact human-review link (display only)

Human operator UI -> existing job approval -> Gateway/Policy -> exact Lambda
                                                        -> provider readback
```

## One PR, three phases, nine milestones

### Phase 5: frontend-ready backend

- [ ] M1: bounded versioned finding/job list/detail and source-health contract;
      same IDs, provenance, plans and outcomes as the existing UI/exports.
- [ ] M2: deterministic evidence intake independent of inference availability;
      explicit ID-based specialist explanation with evidence-aware cache.
- [ ] M3: bounded execution failures, safe diagnostics and local Host/request
      guards; preserve single-writer stores and no automatic mutation retry.

### Phase 6: restricted MCP and real LibreChat

- [ ] M4: six exact MCP tools: list_findings, get_finding, get_source_health,
      explain_finding, list_jobs, get_job. No generic proxy or action endpoint.
- [ ] M5: inspect installed LibreChat/topology, configure one scoped personal-lab
      integration and prove a real conversation invokes the backend.
- [ ] M6: chat opens an exact finding/job in the human UI; navigation never
      mutates. Human edits/decisions remain explicit; chat reads their results.

### Phase 7: integrated acceptance and handover

- [ ] M7: real Config -> chat -> explanation -> operator view/plan -> history ->
      restart/reload proof; identify reused versus freshly executed evidence.
- [ ] M8: focused injection/forged-ID/no-mutation/timeout/partial/replay checks,
      plus measured invocation/cache/latency and available token counters.
- [ ] M9: concise topology/config/runbook, five demo prompts, honest limits,
      current SPEC/CONTEXT and one exact-head release proof/handoff.

Issue #17 contains acceptance criteria and controls; do not duplicate its
full specification into additional documents. Use the official LibreChat/MCP
documentation and the installed runtime, not assumptions about latest features.

## Non-negotiable boundaries

Personal standalone lab only, approved identity and Singapore Region. Keep the
retained exact demo SG action as the only AWS mutation capability. MCP cannot
create/approve/reject/execute jobs, save plans, rearm resources, select arbitrary
AWS APIs or write the local stores. The adapter calls the single backend.

No new AWS resources/IAM/service enablement, company data, public exposure,
multi-account work, second remediation, database/workflow framework or new
frontend. Preserve existing LibreChat agents/chats/configuration. Credentials,
private identities, local state and raw browser evidence stay outside Git.

## Delivery and proof

Amit requested a 5-6-hour engineering-sized package instead of small separate
handoffs. This is scope sizing, not a minimum elapsed runtime or a promise.
Finish all milestones without artificial delays or added busywork.

Use focused checks during development. Then one final validation/public-safety/
diff/status batch and one implementation push by default. Local commits may
separate phases for review; do not publish or request review after each phase.

One real connected browser scenario plus focused API/MCP tests is preferred to
a new browser framework. A working MCP client alone is NOT LibreChat proof.
If a real access/topology gate blocks integration, finish independent approved
work and return one precise BLOCKED_INTEGRATION handoff, not a fabricated PASS.

ChatGPT reviews the full final diff and evidence, merges when eligible and
continues the standing GitHub workflow. Codex does not self-merge.
