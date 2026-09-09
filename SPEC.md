# Specification

Status: complete — Phase 0B.3 PASS

## Problem

Prove that AgentCore Policy makes the final deterministic authorization
decision for one exact tool reached through the retained AgentCore Harness.

## Scope

Create one harmless Lambda tool, expose it through one AWS-IAM AgentCore
Gateway, and attach one ENFORCE Policy engine. Reuse the retained Nova 2 Lite
Harness from Phase 0B.2a.

## MUST

- `dev` input is permitted and reaches Lambda exactly once.
- `prod` input is denied and does not add a Lambda invocation.
- The Harness exposes only the one Gateway tool; built-in tools remain absent.
- The Lambda validates its bounded input and makes no external change.
- Record sanitized live evidence, cost dimensions, and retained resources.

## MUST NOT

- Do not add a UI, generic AWS action, real remediation, Memory, Browser, Code
  Interpreter, Registry, WAF, or multi-agent behavior.
- Do not use company, production, or Organizations-management resources.
- Do not commit account IDs, ARNs, endpoints, session IDs, credentials, or raw
  private evidence.

## Verification

- One Harness `dev` call returns the harmless Lambda marker and the Lambda
  invocation delta is exactly one.
- One Harness `prod` call returns a Policy denial and the Lambda invocation
  delta remains zero.
- Live readback shows Gateway `READY`, Policy `ACTIVE`/ENFORCE, the exact target,
  and a Harness allowlist containing only that target tool.

## Stop Gates

- Stop for identity or Region mismatch, unclear/unbounded recurring cost,
  ambiguous retained-resource ownership, policy not in ENFORCE mode, or any
  request to broaden the tool beyond the fixed synthetic input.
