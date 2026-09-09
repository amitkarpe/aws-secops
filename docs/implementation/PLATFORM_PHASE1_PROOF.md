# Platform Phase 1 proof

Date: 2026-09-10

Authority: Issue #9 / PR #10

Private AWS identities, ARNs, endpoints, resource names, session identifiers,
and raw service responses remain outside this public repository.

## M1–M3 — Intake, adapters, and specialist routing: PASS

The existing loopback app accepts same-origin JSON or CSV content at
`POST /api/import`. Server-side limits remain 256 KB and 100 records. The
request carries only file content, a basename, and one of two server-owned
adapter names; path-like filenames, other origins, malformed fields, and
unsupported values are rejected.

Two public-safe fixtures prove the explicit mappings:

| Source | Adapter input | Specialist | Result |
| --- | --- | --- | --- |
| CloudSCAPE-style | JSON compliance record | Compliance Agent | PLAN_ONLY |
| VAPT-style | CSV vulnerability record | Vulnerability Agent | PLAN_ONLY |

Both records join the same bounded backlog. Server-owned routing selects one
of two distinct system instructions and invokes Nova 2 Lite through the
retained AgentCore Harness once per import batch. Imported JSON is explicitly
untrusted evidence. The response appears in the existing Agent explanation.

Each invocation overrides allowed tools with the exact nonmatching name
`__pilot_explanation_no_tools__`; the CLI omits an empty-string allowlist.
This exposes no built-in or registered MCP tools. Any returned tool-use event
or tool result fails the import before backlog/state publication. Resources,
IAM, and the retained Harness configuration are unchanged.

Correction validation command:

```bash
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 ./scripts/pilot-v1.sh specialist-smoke
```

Two live invocations passed: Compliance Agent explained the synthetic
CloudSCAPE retention control and configuration review; Vulnerability Agent
explained VAPT-DEMO-0001 and a package upgrade/validation plan. Both named their
source, returned zero tool calls, remained PLAN_ONLY, and made no claim of
completed remediation. The real HTTP approval attempt returned 400. Result:
`PLATFORM_SPECIALIST_SMOKE=PASS`. No AWS infrastructure mutation occurred.

## M4 — Eligibility and governed action: PASS

Eligibility requires all of the following: AWS provider origin, `AWS EC2`,
`SECURITY_GROUP`, `dev`, the exact public TCP/22 control, and current
`NON_COMPLIANT` status. Therefore imported evidence cannot imitate a supported
AWS finding. A direct approval attempt after an import returns HTTP 400 before
Gateway or Lambda execution.

The retained personal-lab proof then confirmed:

- human Reject: no remediation call and provider remains `NON_COMPLIANT`;
- synthetic `prod`: Gateway Policy `DENY`, no change;
- human-approved `dev`: Gateway Policy `ALLOW`, exact Lambda action, provider
  re-read `COMPLIANT`;
- final reset: the dedicated unattached demo Security Group returned to
  `NON_COMPLIANT` for the next demonstration.

No second AWS mutation capability was added.

## M5 — Operations view, export, and proportional proof: PASS

The shared screen and exports now show source, specialist route, severity,
status, and `REMEDIATION_SUPPORTED` versus `PLAN_ONLY`. Backlog groupings use
the same deterministic finding objects as CSV and Markdown exports.

Final validation:

- 31 deterministic tests after the specialist correction: PASS;
- live API/provider sequence: CloudSCAPE import, VAPT import, plan-only block,
  SG finding, Reject, Policy DENY, DEV ALLOW, S3 read, backlog, export: PASS;
- retained demo SG after reset: `NON_COMPLIANT`, zero attachments;
- headless browser-visible smoke at `http://localhost:3340/`: PASS;
- public-safety review and `git diff --check`: PASS.

The correction used the two-invocation API smoke above. The earlier full SG
and browser proofs cover the unchanged action path and layout; they were not
repeated for this explanation-only change.

Private browser and live-service evidence remains under
`/home/user/.AGENTS-temp/aws-secops/platform-phase1/` and is not committed.
