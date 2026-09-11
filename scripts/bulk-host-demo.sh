#!/usr/bin/env bash
# Retained EC2 only. Explicitly reset the owned terminal fleet for the next demo.
set -euo pipefail
if [[ ${1:-status} != reset ]]; then
  curl --fail --silent http://localhost:4444/api/v1/list_batches
  exit
fi
[[ $EUID == 0 ]]
[[ $(systemctl show aws-secops-bulk.service -p User --value) == ssm-user ]]
[[ $(systemctl show aws-secops-bulk.service -p WorkingDirectory --value) == /opt/aws-secops-bulk ]]
curl --fail --silent http://localhost:4444/api/v1/list_batches | python3 -c '
import json,sys
b=json.load(sys.stdin)["items"][0]
assert b["context"]["mode"]=="LIVE" and b["context"]["profile"]=="vagent"
assert not b["execution_active"] and not any(b["counts"].get(k) for k in ("PENDING","APPROVED","RUNNING","UNKNOWN"))
print("TERMINAL_FLEET_RESET_GATE=PASS")'
systemctl stop aws-secops-bulk.service
cd /opt/aws-secops-bulk
sudo -H -u ssm-user env SECOPS_BULK_SDK=1 AWS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt .venv/bin/python scripts/bulk-demo.py reset --manifest /var/lib/aws-secops-bulk/manifest.json --batch-state /var/lib/aws-secops-bulk/batch.json
systemctl start aws-secops-bulk.service
sleep 3
curl --fail --silent --max-time 240 -H 'Content-Type: application/json' -H 'Origin: http://localhost:4444' -d '{}' http://localhost:4444/api/bulk/new-preview | python3 -c '
import json,sys
b=json.load(sys.stdin); assert b["decision"]=="PENDING"
print("DEMO_READY: "+str(b["total"])+" non-compliant owned demo buckets; fresh native approval required")'
