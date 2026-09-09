# Pilot v1.1 proof

Date: 2026-09-10

Region: Asia Pacific (Singapore), `ap-southeast-1`

Private AWS identities, ARNs, endpoints, resource names, session identifiers,
and raw service responses remain outside this public repository.

## M1 — One-command smoke validation: PASS

The repo-owned command below starts the real loopback HTTP handler on an
ephemeral port, exercises the application API, and reads provider state after
every stateful decision:

```bash
AWS_PROFILE=amit AWS_REGION=ap-southeast-1 ./scripts/pilot-v1.sh smoke
```

One live run proved:

- Security Group finding: `NON_COMPLIANT`;
- human Reject: provider unchanged and no Gateway remediation call;
- synthetic `prod` approval: Gateway Policy `DENY`, provider unchanged;
- `dev` approval: Gateway Policy `ALLOW`, exact remediation once, provider
  `COMPLIANT`;
- S3 baseline: read-only and provider-backed;
- final reset: exact dedicated unattached Security Group returned to
  `NON_COMPLIANT`.

The command ended with `PILOT_V1_1_SMOKE=PASS` and left zero local listener.

## M2 — Common finding contract: PASS

`pilot_v1.findings` defines one bounded provider-neutral contract used by the
existing Security Group and S3 results. It includes provider/source,
resource type and identity, environment, control, severity, status, evidence,
recommendation, and observation time, plus optional owner and target fields.

The import path accepts JSON or CSV, caps a file at 256 KB and 100 findings,
rejects missing/unknown fields and unsupported status/severity/environment
values, and accepts the public-safe samples under `examples/`. The source names
in those samples illustrate future mapping only; no VAPT, CloudSCAPE, Config,
Inspector, or Security Hub integration was added.

## M3 — Management compliance backlog: PASS

The same bounded common findings now feed a deterministic backlog summary and
the single-user UI. The screen shows total open findings, high/critical count,
bounded finding count, source and resource-type groupings, the ten highest
priority/oldest open findings, and one recommended focus derived from the top
record. No model calculates or changes these management values.

Provider rechecks upsert the same SG/control record, so successful remediation
closes the open finding instead of creating a duplicate. The summary is also
available from `GET /api/backlog` for a small API-first check.

## M4 — Allowlisted multi-bucket S3 assessment: PASS

The existing S3 read Lambda now owns a fixed allowlist of two empty Pilot
buckets and accepts no bucket input from the caller or model. The evaluator is
sequential and capped at five unique buckets. It returns aggregate counts and
only failed-control details to Harness, while retaining deterministic provider
reads for all five controls per bucket.

One live Harness invocation selected the exact S3 Gateway tool once and
returned:

| Measure | Result |
| --- | ---: |
| Allowlisted buckets checked | 2 |
| Provider controls checked | 10 |
| PASS | 9 |
| FAIL | 1 |
| S3 mutations | 0 |

The original bucket remained 5/5 compliant. The second empty demo bucket has
Block Public Access, default encryption, TLS-only policy, and owner-enforced
object ownership; it intentionally leaves versioning not enabled, producing
one safe backlog exception. The Lambda IAM policy names only the two bucket
resources. Private names and raw responses remain in the evidence directory.
