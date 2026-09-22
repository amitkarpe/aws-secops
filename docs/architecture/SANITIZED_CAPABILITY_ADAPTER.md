# Sanitized capability adapter

Authority: Issue #178; Issue #170 M1.

## Purpose

The Compliance Agent needs to know which generic controls a private catalog can
detect, explain, prepare, remediate, and verify without publishing the catalog
itself. The adapter accepts only a small sanitized contract and emits stable
public-safe metadata. It does not ingest findings, account inventory, policy
text, internal mappings, owners, or private source paths.

The public registry contains exactly:

| Control key | Resource type | Current product ceiling |
| --- | --- | --- |
| `s3_ssl` | `AWS::S3::Bucket` | EXPLAIN |
| `s3_logging` | `AWS::S3::Bucket` | EXPLAIN |
| `s3_backup` | `AWS::S3::Bucket` | EXPLAIN |
| `restricted_ssh` | `AWS::EC2::SecurityGroup` | VERIFY |

The three generic S3 entries describe DETECT/EXPLAIN catalog support only. They
do not map to the existing S3 Block Public Access executor and cannot be
prepared, remediated, or verified by this milestone. `restricted_ssh` may point
only to the already-existing governed path.

## Fail-closed contract

[`capability.schema.json`](https://github.com/amitkarpe/aws-secops/blob/main/agents/compliance-agent-v1/capability.schema.json)
defines the machine-readable public contract. The runtime validator is stricter:

- exactly four approved control/resource pairs;
- exact top-level, source, and record fields;
- contiguous capability progression;
- declared state must match its support flags;
- local product ceilings override broader source claims;
- remediation requires both independent human approval and AWS service
  verification;
- unknown, malformed, duplicated, private-extra, or over-privileged input is
  rejected.

Unknown lookup keys return a generic `unsupported` read-only decision and are
not reflected into output.

## Product integration

The validated summary is added to the existing Compliance Agent read packet and
structured response. Capability questions receive a compact native card. No new
MCP tool is registered and the current four tools remain unchanged.

The adapter can say that an existing governed path is technically supported,
but every decision returns `execution_authorized=false`. It cannot accept an
approval decision, create a batch, select a resource, dispatch execution, or
call AWS. Native human approval and the existing executor remain separate
authorization and mutation boundaries.

The outer agent instructions explicitly prevent `s3_ssl`, `s3_logging`, and
`s3_backup` from being routed to the S3 Block Public Access planner. Unknown
controls stay unsupported and read-only.

## Privacy and scope

The checked-in fixture is synthetic generic capability metadata, not a copy of
the private catalog. Tests use no private mappings or findings. This milestone
does not implement Issue #170 M2 query, pagination, export, or 1K work and makes
no IAM, OIDC, network, deployment, or AWS mutation change.
