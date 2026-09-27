# Persistent AWS MCP evidence adapter

Authority: Issue #176; parent research Issue #130.

## Current architecture and gap

Compliance Agent v1 reads its authoritative four-account/two-control matrix
from the strict loopback unified Config backend. Deterministic code validates
the complete matrix before the tool-free AgentCore Harness receives an evidence
packet. Account aliases are public-safe routing labels; private account identity
and runtime credentials stay outside model context. Governed remediation remains
a separate frozen-plan, native-approval, bounded-execution path.

The persistent AWS MCP runtime proved in `amitkarpe/aws-platform#48` can perform
read-only Config, S3, Security Group, Inspector and CloudTrail investigation.
That proof did not provide this repository with a stable normalized contract,
identity-mismatch handling, pagination limits, or an integration/fallback gate.

## Boundary

`PersistentMcpEvidenceProvider` fills that gap without replacing the current
Config backend. It accepts only four enumerated queries:

- Config compliance summary;
- S3 Public Access Block posture;
- Security Group unrestricted-SSH exposure;
- Inspector status and finding-count summary.

There is no service, operation, script, role, Region, resource selector, or
arbitrary parameter supplied by the model. A server-owned transport maps each
enum to the fixed upstream AWS MCP read. The transport interface is internal;
it must not be registered as a model tool.

Every page carries the AWS account identity verified by the transport. The
adapter compares it with the server-owned registered account identity before
normalization. Output contains the LAB alias and a one-way public reference,
not the raw account identity. Pagination is limited to three pages, 50 items
per page, and 100 normalized items overall.

The machine-readable envelope is
[`evidence-provider.schema.json`](https://github.com/amitkarpe/aws-secops/blob/main/agents/compliance-agent-v1/evidence-provider.schema.json).
It preserves source/provenance and reports exactly one state:

- `AVAILABLE` — bounded read completed;
- `PARTIAL` — useful evidence exists but the source or local bounds truncated it;
- `UNAVAILABLE` — identity, transport, shape, pagination, or sensitive-material
  validation failed.

Unavailable evidence never becomes CLEAR/PASS and never triggers another tool.
Transport exception text and raw upstream payloads are not returned. Credential,
token, authorization and secret-shaped fields fail the page closed.

## Integration gate

Live integration is disabled by default. The repository gate returns true only
for the exact server-side value:

```text
SECOPS_PERSISTENT_MCP_EVIDENCE_ENABLED=1
```

Issue #176 does not set that value, implement an OAuth/session transport, add a
LibreChat tool, or change the current Compliance Agent read path. A later
bounded integration must first verify the selected MCP connection with STS,
bind the expected registered account identity server-side, and keep all auth
material outside output and model context.

Routing when a future integration is explicitly approved:

1. Use the unified Config backend for the stable four-account/two-control status
   and remediation-planning contract.
2. Use persistent MCP only for an explicit supported investigation family.
3. If MCP is disabled or unavailable, return `UNAVAILABLE`; do not silently
   substitute stale evidence or infer compliance.
4. Cache only the normalized envelope for a short product-defined TTL. Never
   cache credentials, tokens, raw MCP responses, or verified raw account IDs.
5. Only the normalized allowlisted items may enter model context. Connection
   identity, pagination tokens, auth material, raw responses and transport
   diagnostics remain server-side.

MCP evidence cannot authorize remediation. The persistent runtime exposes only
read authority, and this adapter has no mutation operation. Any change still
requires the existing frozen scope, native human approval, bounded executor,
AWS service readback and independent Config evaluation.

## Fixture proof

Synthetic fixtures cover Config, S3, Security Group and Inspector evidence.
Tests prove deterministic normalization, source/provenance, identity mismatch,
bounded/partial results, sensitive-material rejection, transport failure,
fixed queries, default-disabled integration and `mutation=false`. No live AWS
read is required for PR validation and no private inventory is committed.
