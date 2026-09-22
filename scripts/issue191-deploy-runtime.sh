#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

backup_dir=/var/lib/aws-secops-bulk/issue191-backup
librechat=/opt/LibreChat
resume="$librechat/api/server/controllers/agents/resume.js"
secret_file=/etc/aws-secops/decision-receipt.env
bulk_dropin=/etc/systemd/system/aws-secops-bulk.service.d/issue191.conf
librechat_dropin=/etc/systemd/system/aws-secops-librechat.service.d/issue191.conf

test -d "$backup_dir"
test -d "$librechat"
test -f /opt/aws-secops/integration/s3-ssl-reject-only-approval-hook.cjs
test -f /opt/aws-secops/integration/native-decision-receipt.cjs
test -f /opt/aws-secops/integration/patch-librechat-native-decision-receipt.cjs
test "$(node -p "require('$librechat/package.json').version")" = v0.8.8-rc1
test "$(systemctl is-active aws-secops-bulk.service)" = active
test "$(systemctl is-active aws-secops-librechat.service)" = active

harness_arn="$(node -e 'const fs=require("fs"),yaml=require("/opt/LibreChat/node_modules/js-yaml"); const c=yaml.load(fs.readFileSync("/opt/LibreChat/librechat.yaml","utf8")); const a=c?.mcpServers?.compliance_agent_v1?.env?.COMPLIANCE_AGENT_V1_HARNESS_ARN; if(!/^arn:aws[a-zA-Z-]*:bedrock-agentcore:[a-z0-9-]+:[0-9]{12}:harness\/compliance_agent_v1-[A-Za-z0-9]+$/.test(a||"")) process.exit(2); process.stdout.write(a);')"
test -n "$harness_arn"

if [[ ! -e "$secret_file" ]]; then
  install -d -o root -g root -m 700 /etc/aws-secops
  receipt_secret="$(openssl rand -hex 32)"
  printf 'SECOPS_DECISION_RECEIPT_SECRET=%s\n' "$receipt_secret" > "$secret_file"
  unset receipt_secret
  chown root:root "$secret_file"
  chmod 600 "$secret_file"
fi
test "$(stat -c '%U:%G:%a' "$secret_file")" = root:root:600
grep -Eq '^SECOPS_DECISION_RECEIPT_SECRET=[a-f0-9]{64}$' "$secret_file"

install_dropin() {
  local path="$1"
  local with_lab_profile="$2"
  local parent
  parent="$(dirname "$path")"
  install -d -o root -g root -m 755 "$parent"
  if [[ -e "$path" ]]; then
    grep -Fxq 'EnvironmentFile=/etc/aws-secops/decision-receipt.env' "$path"
    if [[ "$with_lab_profile" == yes ]]; then
      grep -Fxq 'Environment=SECOPS_LAB_PROFILE=amit' "$path"
    fi
  else
    if [[ "$with_lab_profile" == yes ]]; then
      printf '[Service]\nEnvironmentFile=/etc/aws-secops/decision-receipt.env\nEnvironment=SECOPS_LAB_PROFILE=amit\n' > "$path"
    else
      printf '[Service]\nEnvironmentFile=/etc/aws-secops/decision-receipt.env\n' > "$path"
    fi
    chown root:root "$path"
    chmod 644 "$path"
  fi
}

install_dropin "$bulk_dropin" yes
install_dropin "$librechat_dropin" no

node /opt/aws-secops/integration/patch-librechat-native-decision-receipt.cjs "$librechat"
COMPLIANCE_AGENT_V1_HARNESS_ARN="$harness_arn" \
  node /opt/aws-secops/integration/install-compliance-v1.cjs "$librechat" "$harness_arn"
unset harness_arn
COMPLIANCE_AGENT_V1_BACKUP_PATH="$backup_dir/compliance-agent-v1.before.json" \
  node /opt/aws-secops/integration/update-compliance-v1-agent.cjs \
    /opt/aws-secops/integration/compliance-agent-v1.json

systemctl daemon-reload
systemctl restart aws-secops-bulk.service
systemctl restart aws-secops-librechat.service
systemctl is-active --quiet aws-secops-bulk.service
systemctl is-active --quiet aws-secops-librechat.service

bulk_pid="$(systemctl show -p MainPID --value aws-secops-bulk.service)"
librechat_pid="$(systemctl show -p MainPID --value aws-secops-librechat.service)"
test "$bulk_pid" -gt 0 && test "$librechat_pid" -gt 0
for pid in "$bulk_pid" "$librechat_pid"; do
  tr '\000' '\n' < "/proc/$pid/environ" | grep -q '^SECOPS_DECISION_RECEIPT_SECRET='
done
tr '\000' '\n' < "/proc/$bulk_pid/environ" | grep -Fxq 'SECOPS_LAB_PROFILE=amit'

actual_digest="$(sha256sum "$resume" | awk '{print $1}')"
test "$actual_digest" = 9a5ea6723b0daddf7812fba7fb03f47f76183889c3e96a6ad827972f2ad9e0a7
status_file="$(mktemp /run/issue191-s3-ssl-status.XXXXXX)"
trap 'rm -f "$status_file"' EXIT
curl --fail --silent --show-error --max-time 180 \
  http://127.0.0.1:4444/api/operator/s3-ssl-status -o "$status_file"
jq -e '
  .version == 1 and .control == "s3_ssl" and .read_only == true and
  .aws_writes == 0 and .resource_identifiers_emitted == false and
  ([.accounts[].alias] == ["lab-dev","lab-poc","lab-qa","lab-sec"])
' "$status_file" >/dev/null
printf '%s\n' 'ISSUE191_DEPLOY=PASS SOURCE_PIN=PASS SECRET_PRESENCE=PASS S3_SSL_READ=PASS AWS_WRITES=0'
