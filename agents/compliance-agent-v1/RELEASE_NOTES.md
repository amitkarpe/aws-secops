# Compliance Agent v1.0.0

Compliance Agent v1 provides a bounded finding-to-remediation demonstration for
four registered personal-LAB accounts and two controls: S3 Block Public Access
and restricted SSH.

## Highlights

- A dedicated, tool-free Amazon Bedrock AgentCore Harness grounds read and
  explanation responses in current four-account AWS Config evidence.
- LibreChat presents native Approve/Reject decisions for one exact frozen
  remediation scope at a time.
- The model cannot choose accounts, resources, roles, Regions, AWS APIs,
  repositories, buildspecs, ports, CIDRs, or arbitrary execution parameters.
- Approved execution uses the fixed CodeBuild/controller path and the existing
  provider guards for the two supported controls.
- One-time exact exclusions are bound into the frozen batch and scope hash with
  user-supplied reason and optional reference/expiry metadata.
- Timeout and reconciliation handling prevents blind redispatch after an
  uncertain result.
- Rich MCP cards provide a concise fleet view, remediation preview, execution
  status, and verification status without duplicating the primary result.

## Acceptance evidence

- Four-account by two-control evidence matrix: PASS.
- Dedicated Harness golden prompts: PASS 5/5.
- Installed read MCP initialization and strict tool boundary: PASS.
- Authenticated S3 Reject-only API E2E: PASS 4/4.
- Authenticated restricted-SSH Reject-only API E2E: PASS 4/4.
- Authenticated exact-exclusion Reject-only API E2E: PASS 4/4.
- Exact-exclusion provider state remained unchanged after Reject: PASS.
- Remediation-execution dispatches after exception Reject: zero.
- Automated Approve decisions: zero.
- Temporary authentication and conversation cleanup: PASS.
- Rich-card sizing and single-next-action regressions: PASS.
- Exception, timeout, and recovery regressions: PASS.

## Verification model

An accepted execution reports the AWS change separately from verification.
Direct AWS service readback is the immediate remediation truth. AWS Config
evaluation remains independent and may converge later.

## Known limitations

- Scope is limited to four explicitly registered personal-LAB accounts and the
  two controls above.
- No generic model-accessible AWS administration or mutation tool is exposed.
- The demo does not claim production identity governance, hostile multi-tenant
  isolation, or arbitrary-resource remediation.
- Operational identifiers remain in authorized technical evidence and are not
  included in these public release notes.

## Release integrity

The publishing workflow creates the immutable `compliance-agent-v1.0.0` tag and
GitHub Release from the exact validated `main` commit supplied by the manual
main-branch dispatch. The workflow fails closed if the tag or release already
exists.

---

For later versions, append a new release section and publish a new immutable
GitHub Release. Do not rewrite already-published release notes.
