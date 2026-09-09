# Context

Status: Phase 0B.3 complete — PASS

## Current Truth

- Phase 0B.2a proved one Nova 2 Lite response through AgentCore Harness in
  Singapore with `allowedTools=[]` and zero tool calls.
- The retained Harness is `READY`; its execution role does not grant direct
  Runtime command execution.
- Phase 0B.3 proved the retained Harness can call one exact Gateway tool.
- Policy permitted `dev` and Lambda executed exactly once; Policy denied the
  synthetic `prod` input and the Lambda invocation delta remained zero.
- The final roles use exact resources, built-in Harness tools remain absent,
  and no direct Runtime-command permission was added.

## Next Action

- Review the Phase 0B.3 evidence in PR #4, then run one fixed no-tool security
  task benchmark comparing Nova 2 Lite with one stronger Nova model.
