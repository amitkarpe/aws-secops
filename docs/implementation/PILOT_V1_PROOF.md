# Pilot v1 proof

Date: 2026-09-09

Region: Asia Pacific (Singapore), `ap-southeast-1`

Private AWS identities, ARNs, endpoints, session identifiers, and raw service
responses are retained outside this public repository.

## M1 — Compliance Agent foundation: PASS

The retained research Harness was reset as the clean Pilot v1 Compliance Agent
foundation and reached `READY` with:

- Nova 2 Lite through the replaceable model configuration;
- the compliance-only system prompt;
- configured tools `[]` and allowed tools `[]`;
- Memory disabled;
- one reasoning iteration for this no-tool acceptance call;
- no `shell`, `file_operations`, Browser, Code Interpreter, or generic AWS tool;
- no `bedrock-agentcore:InvokeAgentRuntimeCommand` permission on its role.

One native AgentCore CLI invocation returned exactly
`PILOT_FOUNDATION_OK`, made zero tool calls, and its Runtime session was stopped
afterward. The CLI summary represents the response as a serialized JSON text
envelope; the product parser unwraps only its `text` field and rejects missing
or invalid text.

Focused Python tests, compilation, and `git diff --check` passed.

## M2 — Real Security Group finding: PASS

One dedicated Pilot v1 Security Group was created in the personal lab VPC. It
is unattached and contains one intentional TCP/22 ingress rule from
`0.0.0.0/0`. The read Lambda is configured with that server-owned Group ID;
the Gateway tool accepts only `environment=dev` and cannot select another
resource, Region, role, action, or AWS API.

The exact `check_security_group` tool was added to the retained AWS-IAM Gateway
and permitted by an ACTIVE Cedar policy only for the fixed `dev` context. The
Harness allowlist contains only that exact read tool. One verbose native
AgentCore CLI invocation produced:

- exact Gateway tool calls: **1**;
- real provider result: **NON_COMPLIANT**;
- evidence: TCP/22 from `0.0.0.0/0`;
- Security Group attachments: **0**;
- AWS mutation by the read tool: **none**.

The assistant explained the provider result and ended with
`STATUS: NON_COMPLIANT`. A direct EC2 provider read independently confirmed the
rule remained present after the M2 call.

The Policy analyzer rejected an initial unconditional read permit as overly
permissive. No invocation occurred under that failed policy. The final tool,
Lambda validation, and Cedar condition all require `environment=dev`; strict
validation then reached ACTIVE without ignored findings.

## M3 — Human-governed remediation: PASS

One separate remediation Lambda and IAM role were added. The role can describe
Security Groups and revoke ingress only on the fixed dedicated demo Group. The
Lambda accepts only the exact `remove_unrestricted_ssh` Gateway tool with
`environment=dev` and `approved=true`, and it can revoke only TCP/22 from
`0.0.0.0/0`. It re-reads EC2 and returns COMPLIANT only after the provider
confirms that rule is absent.

The ACTIVE Cedar permit binds the exact tool and Gateway and requires both the
fixed `dev` environment and explicit approval boolean. The Gateway remains in
Policy ENFORCE mode.

Live acceptance results:

| Path | Gateway/Policy | Remediation Lambda | Provider result |
| --- | --- | ---: | --- |
| Human Reject | not called | 0 | unchanged NON_COMPLIANT |
| Synthetic PROD + Approve | DENY by default | 0 | unchanged NON_COMPLIANT |
| DEV + Approve | ALLOW | 1 | COMPLIANT |

Lambda START-event evidence over the complete decision window contained
exactly one remediation invocation. The fixed Security Group remained
unattached. No instance, ENI, route, public IP, workload, or other Security
Group rule was changed.

The direct Gateway client passes short-lived SigV4 credentials to `curl` over
stdin rather than command arguments. It accepts the native JSON-RPC denial only
for error code `-32002` with the expected Policy denial markers; other errors
do not count as DENY proof.

## M4 — Verification, audit and thin UI: PASS

A dependency-free Python loopback service and static manager UI now expose the
complete governed path at the repo-assigned local port. The UI does not execute
AWS APIs itself: it calls the Pilot service, which preserves the Harness,
Gateway, Policy, exact-tool, and provider-read boundaries from M1–M3.

One real headless-browser run used the visible controls and proved:

| Visible action | Final stage | Policy | Provider | Changed AWS |
| --- | --- | --- | --- | ---: |
| Check real SG | FINDING | NOT_CALLED | NON_COMPLIANT | false |
| Reject | REJECTED | NOT_CALLED | NON_COMPLIANT | false |
| Policy DENY test | DENIED | DENY | NON_COMPLIANT | false |
| Approve DEV | COMPLETED | ALLOW | COMPLIANT | true |

The final compact audit displays the original provider finding, agent
recommendation, human decision, native Policy result, exact Gateway tool,
independent provider verification, and whether AWS changed. The one approved
change was the exact demo-owned TCP/22 rule; the Group remained unattached.

`scripts/pilot-v1.sh` provides the repeatable operator boundary: `status`
verifies profile/Region/identity and provider state, `rearm-sg` restores only
the fixed unattached demo finding, and `serve` starts the UI on loopback. Raw
browser images and live identities remain in the private evidence directory.

## M5 — S3 relevance and pilot packaging: PASS

One dedicated empty demo bucket was configured with five deterministic controls:

| Provider control | Live result |
| --- | --- |
| Bucket Block Public Access, all four flags | PASS |
| Default server-side encryption | PASS |
| Versioning | PASS |
| TLS-only bucket policy | PASS |
| Bucket-owner-enforced object ownership | PASS |

A separate 128 MB read Lambda and role can call only the five required
bucket-control APIs on that fixed bucket. The Gateway target exposes only
`check_s3_baseline(environment=dev)`. Its strict Cedar policy reached ACTIVE,
and the Gateway remains in ENFORCE mode.

The Harness allowlist now contains exactly the SG read tool and S3 read tool;
no remediation, shell, file, browser, Code Interpreter, or generic AWS tool is
model-selectable. One native Harness invocation selected the S3 tool exactly
once, returned five PASS results and `STATUS: COMPLIANT`, and reported mutation
`none`. A real browser click received HTTP 200 and displayed all five PASS
controls, Policy ALLOW, provider COMPLIANT, and changed AWS `false`.

The retained-resource inventory, cost notes, operator runbook, 3–5 minute demo
script, and PROVEN/PROPOSED/LATER status are now tracked under `docs/`.
