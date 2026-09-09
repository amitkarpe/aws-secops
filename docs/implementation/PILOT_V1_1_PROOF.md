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
