# Named UI deployment — PR #18

## Approved design

Amit approved option 1 on 2026-09-10: one Nginx on the retained personal-lab
EC2, preserving the legacy LibreChat address and stores. Two new CNAMEs point
to the unchanged legacy A record. No additional EC2, load balancer, VPC, NAT,
database or application writer was created.

| Entry | Routing and boundary |
| --- | --- |
| Legacy HTTP name | Preserved route to LibreChat |
| New chat name | HTTP 308 to HTTPS; existing LibreChat login |
| New operator name | HTTP 308 to HTTPS; separate single-user Basic login |
| LibreChat backend | Host loopback port 3333, systemd managed |
| Operator backend | Existing host loopback port 3340, same sole stores |

Ingress 443 uses exactly the pre-existing port-80 trusted source /32. Access
from other networks is intentionally unavailable. No internet-wide ingress was
added. Use the new HTTPS chat URL for credentials; legacy HTTP is retained for
compatibility, not recommended for login. Names and resource identities are
private deployment inputs, not committed constants.

The operator proxy authenticates every request. It rejects POSTs with a missing
or different Origin before rewriting the upstream Host/Origin to the existing
loopback contract. Authorization is stripped upstream. Backend JSON validation
and the exact human approval/Gateway boundary remain unchanged. Chat's six
tools cannot approve or execute. SECOPS_REVIEW_ORIGIN changes displayed links
only, never the MCP backend request destination.

## Deployment sequence

Use AWS_PROFILE=amit and AWS_REGION=ap-southeast-1; privately verify STS against
the retained Pilot state. Read back the exact instance, role, ingress and DNS
before changing anything. Do not use these scripts to adopt an unrelated host.

1. Generate a private payload with `python3 scripts/prepare-public-ui.py
   --chat "$CHAT_HOST" --ops "$OPS_HOST" --legacy "$LEGACY_HOST"
   --private-dir "$PRIVATE_DIR"`. The private directory contains the generated
   operator credential and a checksum-verified POSIX SSM payload. Do not print,
   commit or upload the plaintext credential. Re-running refuses rotation.
2. Give the retained role certificate-renewal access only: ListHostedZones;
   GetChange on Route53 changes; ChangeResourceRecordSets on the exact zone,
   restricted to TXT UPSERT/DELETE for the two exact `_acme-challenge` names.
   This role cannot create the application CNAMEs or alter legacy DNS.
3. Validate `prepare.commands` with `/bin/sh -n`; execute through the shared
   SSM runner on the verified instance. This stages the repository provisioner,
   installs Nginx/Certbot, and prepares a new service without stopping port 80.
4. Run on that host: `python3 integration/public-ui/provision.py handoff
   --config .runtime/edge.json`. It verifies the old listener's command/cwd,
   moves LibreChat to loopback 3333 and starts Nginx. Verify legacy health.
5. Add HTTPS ingress matching the existing trusted source, without modifying
   port 80. Run provisioner `tls` with the same config. Certbot uses DNS-01,
   so certificate validation does not require opening port 80 to the world.
6. With CHAT_HOST, OPS_HOST, LEGACY_HOST, ZONE_ID, PRIVATE_DIR and AWS_PROFILE
   exported, run `bash scripts/subdomain-dns.sh plan`, inspect privately, then
   `bash scripts/subdomain-dns.sh apply`. Conflicting existing records stop;
   exact matching aliases are a no-op. Read back both aliases and unchanged
   legacy A record.
7. Install the reader configuration with SECOPS_REVIEW_ORIGIN set to the new
   HTTPS operator origin using `node integration/install-reader.cjs
   /opt/LibreChat --native-bedrock`; restart aws-secops-librechat. Existing
   agents/chats remain intact; no change to their model or tool selection.

The installer and provisioner intentionally stop on unexpected configuration;
they are a bounded retained-host deployment, not a generic provisioning system.

## Acceptance — 2026-09-10

- Legacy DNS record unchanged; legacy HTTP config endpoint: 200.
- Both new HTTP entries: 308; HTTPS chat config: 200; unauthenticated ops: 401.
- Actual Playwright HTTPS login using a disposable LibreChat user: PASS.
- Real Nova reader conversation called MCP, returned a finding and the exact
  HTTPS operator link; authenticated browser opened that review screen: PASS.
- Operator authenticated page and finding API: 200.
- Missing Origin, unrelated Origin and spoofed loopback Origin POSTs: 403.
- Correct-origin invalid plan JSON reached backend validation: 400; wrong
  Content-Type: 415. Job query unchanged before/after these probes.
- Nginx, LibreChat and existing backend active; certificate present; automatic
  renewal timer enabled. Host certificate issuer: Let's Encrypt; expiry
  2026-12-09. Renewal itself and machine reboot were not exercised in this pass.
- Local Chromium initially rejected the network inspection CA. The existing
  system-trusted CA was imported into an isolated test NSS store and supplied
  to Node via NODE_EXTRA_CA_CERTS. No ignoreHTTPS/certificate bypass flag was
  used; deployed TLS settings were not weakened.
- 52 deterministic tests, Python/Node/Bash syntax checks and diff check PASS.
- No SG remediation, sync, new job or AWS workload mutation in this hosting
  acceptance. Earlier milestone action evidence is not relabelled as a new run.

Private screenshots, operator-login.json, DNS/ingress readbacks and SSM evidence
are under the operator's private `aws-secops/subdomains` evidence directory.
Screenshots contain real findings and must not enter this public repository.

## Operation, retention and rollback

Use `systemctl status nginx aws-secops-librechat aws-secops-backend` on the
retained host. Certbot renewal timer is enabled; its deploy hook validates and
reloads Nginx. Monitor renewal failure before expiry. No renewal email was
registered. Protect and retain the private credential file; rotate the operator
hash intentionally, not by re-running prepare.

Rollback: run provisioner `rollback` with the existing private config. It stops
only the new edge/LibreChat units and starts the legacy process on port 80.
Verify HTTP health before claiming recovery. It does not delete stores,
certificates, credentials or DNS. New HTTPS names will be unavailable during
rollback; DNS/443/policy removal is a separate exact reviewed action. Rollback
code is provided but was not executed against the successful live deployment.

Retained additions: two CNAMEs, one source-restricted HTTPS rule, one narrowly
scoped certificate IAM policy, Nginx/Certbot and one LibreChat service unit.
Review TTL: 10-10-26; owner Amit; no automatic deletion. DNS and inline IAM
policies do not support resource tags, so lifecycle is recorded here. Existing
EC2/storage charges continue; no additional hourly compute/LB service was
introduced. DNS queries, transfer, logs and inference remain usage dependent;
this pass does not claim a new billing measurement.
