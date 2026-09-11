# S3 demo: find → approve → apply fix → verify

Open the existing **S3 Compliance Demo** agent in LibreChat, not the separate
**AgentCore Governance Demo** Security Group agent. The S3 agent is updated
centrally; Amit does not need to recreate it. Private URLs stay in the meeting copy.

## Five prompts — stay in the same chat

Use a prepared non-compliant batch. Answers must show the actual fleet size.

1. **“Check the current S3 demo batch. Show how many buckets need a fix.”**
   Expected: PENDING batch; BlockPublicAcls is false. No AWS change.
2. **“Explain the finding and recommend the exact fix. Do not apply it yet.”**
   Expected: enable all four bucket-level Block Public Access settings.
   This is one control, not complete AWS compliance.
3. **“Apply the fix to this exact current batch.”**
   Expected: native ASK card with batch, count and scope hash.
   Select **Reject**, then **Submit**. Expected: cancelled/rejected tool;
   zero Gateway calls and zero fixes. The batch stays PENDING because
   LibreChat stops the tool before it reaches the worker. This is not a failure.
4. **“Apply the fix to this exact current batch.”**
   Expected: a fresh ASK card. Select **Approve**, then **Submit**.
   Expected: execution started, then APPROVED/RUNNING progress. This is not
   yet compliance proof. No separate Operator page or Run button is needed.
5. **“Read the latest batch again. Show verified compliant, remaining, denied,
   failed and unknown counts.”**
   Expected after completion: verified N/N from independent S3 reads.
   Repeat this read-only prompt while active. Never repeat approval simply
   because the browser disconnected or the response was delayed.

## What governance proves

Human approval and AWS authorization are separate gates:

`Native ASK → frozen batch → Gateway Policy → exact Lambda → S3 readback`

- Reject: no execution tool reaches the worker; zero Gateway dispatch.
- Approve: starts only the displayed immutable batch. No Approve All.
- Gateway DENY: target not invoked; distinct from a timeout or tool failure.
- COMPLETED: independent provider read confirms all four settings true.
- UNKNOWN: uncertain outcome; reconcile by reading AWS, never blindly retry.
- SKIPPED: already compliant; no unnecessary write.

The model cannot choose a bucket, AWS profile, API operation or policy decision.
The executor accepts only `batch_id` and `approval_hash`; the server owns scope.
Eight existing reader tools remain read-only. Operator UI is optional for
per-item evidence, export, reconciliation and explicit continuation.

## Deployment and recovery

The sole bulk writer runs on the retained EC2 as `aws-secops-bulk.service`,
under `ssm-user`, on loopback 4444, using the existing private vagent profile.
Original backend, LibreChat, legacy route and SG demo are preserved.
**WSL is no longer required. Do not restart its retired writer or bridge.**

Repo-owned components:

- `scripts/prepare-inline-bulk.py`: private reviewed SSM staging payload;
  `--update-code-only` preserves the current manifest and journal.
- `integration/install-bulk-executor.cjs`: one executor, native ASK matchers,
  and current-batch approval hook.
- `integration/bulk-governed-agent.json`: centrally maintained agent config.
- `scripts/provision-bulk-gateway.py`: plan by default; `--create` deploys
  scoped resources, `--replace-scope` updates the exact approved allowlist.
- `scripts/validate-bulk-runtime.py`: status-only by default;
  `--interrupt` runs ten-bucket recovery; `--execute 10|50|100` explicitly
  runs API validation. Neither option constitutes native human-click proof.

The worker saves RUNNING before dispatch. After interruption, unfinished items
become UNKNOWN; restarting never automatically resumes execution. Read-only
reconciliation comes first, then explicit continuation of remaining approved
items. Failed items require a fresh provider preview and separate approval.
Browser closure does not stop the worker. A journal lock prevents two writers.

## Repeat the demo

On the retained EC2, one command prepares the next demonstration:

```bash
sudo bash /opt/aws-secops-bulk/scripts/bulk-host-demo.sh reset
```

Expected: `DEMO_READY`, the actual fleet count, and a fresh PENDING preview.
It refuses active/uncertain work and never approves or executes a fix.
If any command fails, stop and inspect the owned worker and journal; do not
blindly repeat reset. Without `reset`, the script only reads current status.

Use only `scripts/bulk-demo.py` with the exact private manifest. Stop the owned
worker first and preserve the terminal journal. Reset changes only
BlockPublicAcls to false on owned empty ACL-disabled buckets; the other three
flags stay true. No objects, public policy or account-protection changes.
Restart and create a fresh preview. Factory arguments remain documented in
BULK_S3_DEMO.md; its older WSL/direct-write instructions are historical.

Live scale is gated **10 → 50 → 100, then stop**. The 1,000-item proof is offline,
not 1,000 live buckets fixed. Retention requires owner/TTL/cost review.
Never delete unrelated resources, profiles, routes or older demonstrations.
