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
