# Native decision receipt boundary (Issue #193)

This is a repository-only implementation for the exact `s3_ssl` reject-only
approval tool. It is **not deployed** and grants no live execution authority.
Issue #191 must separately wire an authenticated prepare/freeze registration
before a live native card can use it; no model-facing registration endpoint is
provided here.

The patch installer accepts only LibreChat `v0.8.8-rc1` and the pinned
`api/server/controllers/agents/resume.js` source digest. It inserts one call
after the existing validated, single-winner approval claim and before
`resumeCompletion`. Other tools return without a receipt call or resume-value
change. Source drift aborts installation.

For the exact tool, the adapter obtains authoritative pending tool input,
native action/generation identity, authenticated user, and final decision. It
sends a signed request to the loopback operator endpoint. The endpoint binds
the request to a registered frozen batch/scope/user and records the terminal
state in an append-only SQLite receipt, atomically with consuming the freeze.
Duplicate, stale, wrong-tool, wrong-scope, and wrong-user decisions fail
closed. Receipts are checked on reopen. No AWS or executor component is
imported by this path.

Both native choices resume as an SDK `reject` result **only after** durable
receipt persistence: human Reject becomes `REJECTED`; human Approve becomes
`APPROVE_BLOCKED` with `LIVE_EXECUTION_NOT_AUTHORIZED`. Neither choice reaches
the tool, CodeBuild, Gateway, Lambda, or an AWS write. If the receipt callback
fails, the claimed generation is terminalized without `resumeCompletion` and
the client receives a bounded failure; it is not retried automatically. The
runtime must supply the same private, at-least-32-character
`SECOPS_DECISION_RECEIPT_SECRET` to the adapter and operator server. Never
store this value in Git.

The receipt database is private runtime state, not public Git evidence. Its
local append-only triggers and hash chain detect ordinary modification, but
are not an external tamper-proof audit service. A future live #191 integration
must register a freeze through trusted server code, prove the exact runtime
patch and native card, and independently confirm provider readback. This PR
does not deploy or claim that live proof.
