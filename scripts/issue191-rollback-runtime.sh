#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

backup_dir=/var/lib/aws-secops-bulk/issue191-backup
librechat=/opt/LibreChat
resume="$librechat/api/server/controllers/agents/resume.js"
resume_backup="$resume.before-issue193-native-receipt"
mode_file="$resume_backup.mode"

test -d "$backup_dir"
test -s "$backup_dir/bulk-runtime.before.tar.gz"
test -s "$backup_dir/compliance-agent-v1.before.json"
test -s "$resume_backup"
test -s "$mode_file"
systemctl stop aws-secops-librechat.service aws-secops-bulk.service
tar -xzf "$backup_dir/bulk-runtime.before.tar.gz" -C /
for relative in \
  pilot_v1/mcp_executor.py pilot_v1/mcp_bridge.py pilot_v1/operator_mcp.py \
  pilot_v1/agentic_evidence.py pilot_v1/codebuild_execution.py pilot_v1/org_config_overview.py \
  pilot_v1/native_decision_receipt.py integration/bulk-approval-hook.cjs \
  integration/install-bulk-executor.cjs integration/native-decision-receipt.cjs \
  integration/s3-ssl-reject-only-approval-hook.cjs integration/patch-librechat-native-decision-receipt.cjs; do
  backup="$backup_dir/opt/aws-secops/$relative"
  if [[ -f "$backup" ]]; then install -D -m 644 "$backup" "/opt/aws-secops/$relative"; fi
done
for relative in integration/install-compliance-v1.cjs integration/update-compliance-v1-agent.cjs integration/compliance-agent-v1.json; do
  backup="$backup_dir/opt/aws-secops/$relative"
  if [[ -f "$backup" ]]; then install -D -m 644 "$backup" "/opt/aws-secops/$relative"; fi
done
cp "$resume_backup" "$resume"
chmod "$(cat "$mode_file")" "$resume"
resume_digest="$(sha256sum "$resume" | awk '{print $1}')"
[[ "$resume_digest" == 54dad95a0e143f5d72857d98c8398743e68e101cab527b38382a7c0d51f10e43 ||
   "$resume_digest" == 6f0f53afbaa06dd65e9558e1595060433e37952ef9b0ad1d4ad57781bcbcf025 ]]
if [[ -f "$librechat/librechat.yaml.before-compliance-agent-v1" ]]; then
  cp -p "$librechat/librechat.yaml.before-compliance-agent-v1" "$librechat/librechat.yaml"
fi
LIBRECHAT_AGENT_BACKUP="$backup_dir/compliance-agent-v1.before.json"
node /opt/aws-secops/integration/rollback-compliance-v1-agent.cjs "$LIBRECHAT_AGENT_BACKUP"
rm -f /etc/systemd/system/aws-secops-bulk.service.d/issue191.conf
rm -f /etc/systemd/system/aws-secops-librechat.service.d/issue191.conf
systemctl daemon-reload
systemctl start aws-secops-bulk.service
systemctl start aws-secops-librechat.service
systemctl is-active --quiet aws-secops-bulk.service
systemctl is-active --quiet aws-secops-librechat.service
printf '%s\n' 'ISSUE191_ROLLBACK=PASS RECEIPT_DB_AND_PRIVATE_KEY_PRESERVED=yes'
