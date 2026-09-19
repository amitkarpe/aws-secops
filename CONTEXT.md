# Agent Context

Repository: `amitkarpe/aws-secops`  
Status: ACTIVE  
Updated: 2026-09-19

> Current-only restart index. Read the latest owning Issue/PR comment for mutable rollout and power state; historical snapshots are not live proof.

## Current Authority

- Issue #114 / PR #115: polish the SecOps Admin Control Center re-arm UX and Config Dashboard navigation.
- Personal-LAB standing authority is active: continue bounded demo implementation/deployment/validation without repeated approval prompts.
- Keep the retained demo host running; do not proactively ask for shutdown after validation. Stop only when Amit explicitly requests a cost-saving shutdown. Never terminate.
- Validate GitHub first, then STS on the exact personal-LAB connection from Issue #106 before AWS work.
- Preserve the existing bounded remediation and human-approval boundaries; no generic rollback/revoke or arbitrary AWS admin API.

## Current UI

- PR #107 merged and its exact static HTML was deployed; independent readback is recorded on that PR.
- Amit supplied an authenticated Operator screenshot and accepted the existing layout. Issue #106 can close on that visual acceptance; the theme is a follow-up, not a new layout.
- PR #109 merged the direct GitHub/AWS MCP operating guidance. Codex is fallback only.
- PR #111 adds a keyboard-accessible Dark mode On/Off toggle, local preference storage, initial system preference, and matching light/dark surfaces. Theme changes have no API side effects.
- Focused Node-VM regression/theme checks and synthetic Chromium desktop/390px/320px checks passed on the candidate. CI, merge and live rollout must be verified from the latest PR evidence; this checkpoint alone does not claim deployment.

## Session Power

Follow [Personal LAB session power](docs/operations/LAB_SESSION_POWER.md).

- Keep the retained host running during active demo work. Do not ask for STOP merely because validation completed.
- Stop only when Amit explicitly requests a cost-saving shutdown; never terminate.
- If a later explicit stop has occurred, start only the same STS-verified retained host when runtime work resumes; verify SSM, services and endpoint/auth health.
- Do not interrupt active work or start the host for repository-only work. Preserve data, disks, journals and configuration.
- Record validation-complete, prompt-delivered and stop-confirmed checkpoints on the owning Issue/PR. Do not infer power state from this file.

## Product and Evidence Boundaries

Exactly `lab-dev`, `lab-poc`, `lab-qa`, `lab-sec`; exactly S3 Block Public Access and restricted SSH. Retained 100-S3 / 10-SG scope stays collapsed/legacy. Current Config evidence and saved historical acceptance remain separate. Browser fetch age is not Config evaluation age.

`Config -> read-only plan -> frozen exact batch -> separate native decision -> fixed CodeBuild/CodeConnections -> existing G/O controller -> exact target sessions -> provider readback -> independent Config convergence`

No generic administration, new controls, SCP changes or Config auto-remediation. Alias-only public output. Issue #100's recorded Reject test withheld executor invocation after ASK; it was not a browser Reject-click test. PR #105 remains a separate open acceptance-doc change whose old CONTEXT edits must not overwrite this active pointer.

## Next

Complete PR #111 validation and static-HTML-only rollout, record readback, then ask Amit to confirm STOP after testing is finished. Read the latest Issue/PR checkpoint first to avoid duplicate rollout or reminders.
