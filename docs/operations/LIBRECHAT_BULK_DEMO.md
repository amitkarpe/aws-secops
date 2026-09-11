# S3 demo: find the gap, approve the fix, verify the result

Use the **S3 Compliance Demo** agent in the named LibreChat deployment.
Do not select the older **AgentCore Governance Demo** agent: that is a separate
single-Security-Group demonstration. The exact private URLs are in Amit's
Windows meeting copy, not this public repository.

## Five-minute operator flow

1. In S3 Compliance Demo, send: **Check the current S3 demo batch. Show the
   non-compliant finding, recommended fix and operator approval link.**
   Expected: five demo buckets; a saved Block Public Access setting is off;
   recommended fix is enabling the four bucket-level settings. No change yet.
2. Open the returned **operator review link** and use the operator login.
   Expected: the exact batch, PENDING 5. Chat login alone cannot authorize AWS.
3. Click **Reject — no dispatch**. Expected: DENIED 5; zero fix dispatches.
4. Click **New preview after terminal batch**. Wait for fresh AWS reads and
   PENDING 5, then click **Approve exact displayed hash**.
   Expected: APPROVED 5; permission saved, not yet fixed.
5. Click **Run / continue approved items**. Expected after completion:
   **Verified: 5/5**, COMPLETED 5, provider-backed per-bucket results.
6. Return to chat and send: **Read the latest batch again. Are all five
   buckets verified compliant? Show the result and review link.**
   Expected: COMPLIANT for this one control, based on the saved AWS readback.

No write tool or approval button is added to chat. Human decisions stay in the
authenticated operator page. A request to approve in chat must return the
review link, not execute a change. Chat reads the saved snapshot and its time;
fresh scans/previews remain explicit operator actions. APPROVED is not COMPLIANT.

## Limits to say out loud

- Five real empty demo buckets, one control. This is not complete AWS compliance.
- The 1,000-item result is offline. Do not describe it as 1,000 live buckets fixed.
- S3 execution uses the exact human-approved CLI provider, not Gateway Policy.
- Reset disables only BlockPublicAcls; the other flags and disabled ACLs remain.
  No objects or public policy are created. See BULK_S3_DEMO.md for reset commands.
- WSL must remain on for this demo. Its sole bulk writer owns the journal and
  vagent credentials. Lost connectivity must show unavailable, not fake success.

## Deployment and recovery

The retained EC2 still owns LibreChat and the original backend. A dedicated SSH
transport through SSM exposes WSL loopback 4444 on EC2 loopback 4444. No AWS
credentials leave WSL, no new ingress or IAM is required, and no second writer
is started. The dedicated public key allows only port 4444 forwarding; command,
PTY and agent forwarding are restricted. Its private key stays on WSL. Pin the
host public key from authenticated SSM inspection, never disable host checking.

1. Start the existing isolated bulk operator with its private manifest/journal.
2. Review the output of `scripts/prepare-bulk-bridge.py --public-key
   <dedicated-public-key> --commands-file <private-command-file>`. Validate the
   payload with `/bin/sh -n`, then use the established SSM runner on the verified
   retained host. This stages code and one restricted transport public key.
3. Set private `BULK_INSTANCE_ID`, `BULK_SSH_KEY`, `BULK_KNOWN_HOSTS` and
   `PILOT_STATE_FILE`, then run `bash scripts/connect-bulk-demo.sh`. Retain the
   process in the existing repo tmux session. Verify remote loopback readiness
   before enabling the edge; process existence alone is not connection proof.
4. On the retained host, run `integration/public-ui/provision.py bulk` with
   the existing private edge config. Four exact bulk paths inherit operator
   authentication and same-origin checks; other paths remain unchanged.
5. Use `integration/install-reader.cjs` with the existing HTTPS review origin
   and `SECOPS_BULK_BACKEND_URL=http://localhost:4444`. Restart only LibreChat.
   The original six tools still use port 3340; two batch readers use port 4444.
6. Use `integration/bulk-reader-agent.json` for the dedicated agent. Grant only
   the intended operator access through native LibreChat permissions; preserve
   old agents/chats. No global sharing or role expansion is needed.

Keep endpoint/account/key/agent identifiers private. The local transport can
be stopped without deleting resources or journals. The edge has a private
pre-bulk backup; restore the exact reviewed previous config and validate/reload
Nginx for rollback. Do not remove legacy routes, stores, credentials or other SSH
keys. A disconnected bridge leaves the bulk feature unavailable.

Automation note: use the actual authenticated browser context for chat tests.
LibreChat's non-browser protection blocked a standalone API sharing probe;
only the exact test-generated ban was removed after confirming its cause.
Global protection was not disabled. Do not create replacement accounts to
evade a ban, clear unrelated bans or weaken the shared login boundary.

AWS reference: [SSH through Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-getting-started-enable-ssh-connections.html).
SSM does not log SSH/forwarded payload content; the batch journal remains the
application's durable decision/result evidence.
