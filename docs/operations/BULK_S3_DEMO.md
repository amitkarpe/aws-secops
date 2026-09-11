# Five-bucket governed compliance demo

## The story to tell your team

“We identify an exact configuration gap, show the affected resources, ask a
human to approve an immutable batch, apply one narrowly defined fix, and verify
each resource directly with AWS. AI can help explain evidence, but cannot give
itself permission to change AWS.”

This demo checks **one control**, not overall AWS compliance: all four
bucket-level S3 Block Public Access (BPA) settings must be true.

The reset makes only `BlockPublicAcls` false. The other three protections stay
true, Object Ownership keeps ACLs disabled, buckets stay empty, and no bucket
policy is permitted. NON_COMPLIANT here means the bucket-level control is not
fully configured; it does **not** mean we published data.

## Live presentation: allow 5–8 minutes

Open **http://localhost:4444/bulk** on the operator workstation. This is the
new isolated `vagent` batch lane; it does not replace the existing remote
LibreChat or Operator UI. If presenting without the runtime, use the private
meeting packet's numbered screenshots in the same order.

| Step | What Amit does | Expected screen/result |
| --- | --- | --- |
| 1 | Click **Read provider & preview** | LIVE, exact resource count 5, immutable approval hash, PENDING 5. No writes |
| 2 | Explain the scope | Only these five empty tagged buckets; only enable four BPA settings. No caller-selected resource/action |
| 3 | Click **Reject — no dispatch** | REJECTED, DENIED 5, verified 0/5. Provider state unchanged |
| 4 | Click **New preview after terminal batch** | Fresh provider reads and a new approval hash; PENDING 5 |
| 5 | Click **Approve exact displayed hash** | APPROVED 5. Approval is saved; no item is executed yet |
| 6 | Click **Run / continue approved items** | Sequential per-item progress. Keep the browser open; Pause stops after the current item |
| 7 | Wait for terminal results | VERIFIED 5/5; each row COMPLETED after independent AWS re-read, or SKIPPED if already compliant |
| 8 | Click **Export current results** | CSV includes batch ID, resource, outcome, change attribution and message |

Do not claim success from “Approved” alone. Success requires provider-verified
results. A mixed batch must show individual FAILED/DENIED/UNKNOWN outcomes,
not a blanket compliant message. UNKNOWN means do not retry blindly; use
**Reconcile UNKNOWN — read only**. No automatic mutation retry occurs.

## Prepare, reset and start commands

Run from `/home/user/git/aws-secops`. Keep PRIVATE outside Git. Commands use
the existing `vagent` profile explicitly; never copy credentials to another host.

```bash
PRIVATE=/home/user/.AGENTS-temp/aws-secops/bulk-preflight

# One-time creation only. Existing manifest causes a stop, not another fleet.
python3 scripts/bulk-demo.py create \
  --manifest "$PRIVATE/demo-manifest.json" \
  --account-file "$PRIVATE/identity-current.json" --count 5 --ttl 18-09-26

# Read-only provider check; expected five NON_COMPLIANT before the demo.
python3 scripts/bulk-demo.py read --manifest "$PRIVATE/demo-manifest.json"

# Start the single writer; first check port 4444 is free.
python3 -m pilot_v1.bulk_server \
  --manifest "$PRIVATE/demo-manifest.json" \
  --state "$PRIVATE/demo-batch.json" --port 4444
```

Before the **next** demonstration, stop the batch UI/server cleanly and ensure
the current batch is terminal, not APPROVED/RUNNING/UNKNOWN. Then:

```bash
python3 scripts/bulk-demo.py reset --manifest "$PRIVATE/demo-manifest.json"
python3 scripts/bulk-demo.py read --manifest "$PRIVATE/demo-manifest.json"
```

Expected: reset succeeds for exactly five manifest/tag/identity/Region-bound
buckets; five NON_COMPLIANT results. Restart the server with the same command.
Use **New preview after terminal batch** to obtain fresh evidence/hash; never
reuse the previous approval. Previous terminal journals are retained privately.
The store retains at most ten previews before requiring an explicit archive
review. Do not delete an audit journal simply to bypass this limit.

## Optional explicit cleanup

```bash
python3 scripts/bulk-demo.py cleanup --manifest "$PRIVATE/demo-manifest.json"
```

Stop the server first. Cleanup refuses buckets that fail exact manifest,
ownership, Region, empty/version/multipart, ACL-disabled or policy-absence
checks. It never empties a bucket or deletes objects. Keep the private manifest
and audit record for recovery; read back deletion before declaring cleanup done.
TTL is a review deadline, not an automatic deletion instruction.

## Scope and presentation honesty

- Five real buckets are the intended live proof; no 1,000-bucket creation.
- The separate offline fixture represents 1,000 items and must be labelled
  OFFLINE. Do not describe that result as AWS scale proof.
- AWS Config is absent in this lab: direct S3 reads supply the evidence.
- `vagent` credits do not establish zero cost. Track request counts and actual
  cost visibility; do not extrapolate billing from a small demo.
- The remote `amit` deployment and existing SG workflow stay unchanged.
- The new local batch UI is not yet proof of an integrated LibreChat batch
  conversation. Report that acceptance separately in PR #21.
- Resource identifiers and real screenshots belong only in the private meeting
  packet, not this public repository.
