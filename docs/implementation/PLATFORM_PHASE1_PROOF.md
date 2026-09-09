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

Both records join the same bounded backlog. Grounded explanations quote the
normalized source, resource, status, control, and recommendation; no model
chooses the specialist route.

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

- 29 deterministic tests: PASS;
- live API/provider sequence: CloudSCAPE import, VAPT import, plan-only block,
  SG finding, Reject, Policy DENY, DEV ALLOW, S3 read, backlog, export: PASS;
- retained demo SG after reset: `NON_COMPLIANT`, zero attachments;
- headless browser-visible smoke at `http://localhost:3340/`: PASS;
- public-safety review and `git diff --check`: PASS.

Private browser and live-service evidence remains under
`/home/user/.AGENTS-temp/aws-secops/platform-phase1/` and is not committed.
