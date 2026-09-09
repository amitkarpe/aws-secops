# Pilot v1 implementation plan

Status: complete — M1–M5 PASS and ready for review

Authority: Issue #5

Base evidence: Phase 0B / PR #4

## Goal

Build one clean, single-user Compliance Agent pilot in the approved personal AWS lab.

The pilot promotes the already-proven AgentCore pattern into product code:

```text
provider finding
-> Harness specialist agent
-> human decision
-> Gateway + Policy
-> exact tool
-> AWS provider verification
-> compact audit/UI
```

## Milestones

### M1 — Foundation

- Compliance Agent on Harness in `ap-southeast-1`.
- Nova 2 Lite initially; model remains replaceable.
- No default Harness built-ins.
- Only exact Gateway tools are exposed.
- Narrow workload IAM and server-owned configuration.

### M2 — Real Security Group finding

- Exact read tool behind Gateway.
- Detect unrestricted TCP/22 on one dedicated demo Security Group.
- Ground explanation in real provider state.
- No remediation in this milestone.

### M3 — Human-governed remediation

- Exact action: `remove_unrestricted_ssh` only.
- Reject -> zero mutation.
- Synthetic PROD / Policy DENY -> zero mutation.
- DEV + Approve + ALLOW -> exact remediation once.

### M4 — Verification, audit and thin UI

- Provider re-read after action.
- Report COMPLIANT only when AWS proves it.
- Compact audit: finding -> recommendation -> human -> policy -> tool -> verification.
- Minimal single-user demo UI; no multi-user platform work.

### M5 — S3 relevance + packaging

- Read-only S3 baseline for one demo bucket across up to five deterministic controls.
- No S3 remediation.
- Add pilot runbook, retained-resource/cleanup inventory, cost notes and short demo script.

## Boundaries

Do not add multi-account onboarding, Organizations/StackSets, Registry dependency, Temporal Policy rollout, broad Security Hub/Config/Inspector enablement, EKS, Supervisor/A2A, multi-user auth, or generic AWS write tooling.

Do not commit lab account IDs, ARNs, private endpoints, credentials, tokens, emails or raw private evidence.

## Working style

- Keep all five milestones in one implementation PR.
- Commit milestone-by-milestone.
- Use AWS MCP / official AWS docs for current behavior and direct AWS CLI for simple setup/readback.
- Reuse Phase 0B patterns, not historical POC plumbing.
- For every AWS mutation: exact scope -> proof -> provider readback.
- Track retained billable resources and cleanup path.

## Final acceptance

```text
real SG finding
-> grounded explanation
-> Reject = no action
-> Approve
-> Policy ALLOW
-> exact remediation
-> provider re-read = COMPLIANT
-> compact audit/UI
```

plus one provider-backed read-only S3 compliance summary and clean pilot operations documentation.
