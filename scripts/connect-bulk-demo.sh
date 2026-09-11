#!/usr/bin/env bash
# Keep the vagent writer/credentials on this host. Forward only its loopback port.
set -euo pipefail
: "${BULK_INSTANCE_ID:?Verified retained instance required}"
: "${BULK_SSH_KEY:?Private dedicated transport key path required}"
: "${BULK_KNOWN_HOSTS:?SSM-verified SSH host key file required}"
: "${PILOT_STATE_FILE:?Retained private identity state required}"
[[ "$BULK_INSTANCE_ID" =~ ^i-[a-f0-9]+$ ]] || exit 1
expected=$(jq -er .accountId "$PILOT_STATE_FILE")
actual=$(aws sts get-caller-identity --profile amit --region ap-southeast-1 --query Account --output text)
[[ "$actual" == "$expected" ]] || { echo 'Retained identity mismatch' >&2; exit 1; }
curl --max-time 5 -fsS -o /dev/null http://localhost:4444/api/v1/list_batches
test -f "$BULK_SSH_KEY" && test -f "$BULK_KNOWN_HOSTS"
echo 'Connecting private bulk demo; keep this process running. No AWS credentials are transferred.'
exec ssh -N -T -i "$BULK_SSH_KEY" -o IdentitiesOnly=yes -o BatchMode=yes \
  -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$BULK_KNOWN_HOSTS" \
  -o ExitOnForwardFailure=yes -o ServerAliveInterval=20 -o ServerAliveCountMax=3 \
  -o "ProxyCommand=aws ssm start-session --profile amit --region ap-southeast-1 --target %h --document-name AWS-StartSSHSession --parameters portNumber=22" \
  -R 127.0.0.1:4444:127.0.0.1:4444 "ubuntu@$BULK_INSTANCE_ID"
