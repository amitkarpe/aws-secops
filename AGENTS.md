# AGENTS.md

## Read Order

1. `AGENTS.md`
2. `CONTEXT.md`
3. `SPEC.md` when work changes a trusted contract, release, environment, or
   external system.

## Rules

- Follow KISS: one problem, one happy path, one command, one proof, one result.
- Preserve existing work. Do not revert unrelated changes or use destructive
  Git commands without explicit approval.
- Keep durable code, decisions, and reports in Git. Do not put secrets,
  credentials, large dependencies, or copied repositories in temporary paths.
- Create a temporary directory or worktree only when isolation is needed.
  A terminal result or `.done` marker alone never authorizes deletion. Remove
  an exact worktree or temporary directory only with owner/controller
  acceptance and explicit cleanup authority; preserve work that is active,
  held, dirty, or unknown.
- Update `CONTEXT.md` when current truth or the next action changes.
- Keep `SPEC.md` small. A worker proceeds inside an approved SPEC and stops on
  a safety, scope, authorization, or evidence failure.

## Global Guidance

When available, use `~/.agent/CORE.md` as the shared machine-wide operating
contract. `~/.codex/AGENTS.md` is a Codex-specific adapter only. Agent OS is
reusable guidance, never automatic project authority; local repository rules
and approved SPECs remain authoritative.
