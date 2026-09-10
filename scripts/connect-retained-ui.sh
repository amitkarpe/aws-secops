#!/usr/bin/env bash
# Open both local UIs through the approved retained host; starts no AWS resources.
set -euo pipefail
profile="${AWS_PROFILE:-amit}"
region="${AWS_REGION:-ap-southeast-1}"
state="${PILOT_STATE_FILE:-/home/user/.AGENTS-temp/aws-secops/pilot-v1/state.json}"
: "${PILOT_EC2_NAME:?Set the existing retained EC2 Name tag privately}"
[[ "$profile" == amit && "$region" == ap-southeast-1 ]] || { echo 'Unexpected deployment context' >&2; exit 1; }
expected=$(jq -er .accountId "$state")
actual=$(aws sts get-caller-identity --profile "$profile" --query Account --output text)
[[ "$expected" == "$actual" ]] || { echo 'Identity mismatch' >&2; exit 1; }
for port in 3340 13080; do
  [[ -z "$(ss -ltnH "sport = :$port")" ]] || { echo "Port $port already occupied; reuse it or inspect its owner" >&2; exit 1; }
done
mapfile -t matches < <(aws ec2 describe-instances --profile "$profile" --region "$region" \
  --filters "Name=tag:Name,Values=$PILOT_EC2_NAME" Name=instance-state-name,Values=running \
  --query 'Reservations[].Instances[].InstanceId' --output text | tr '\t' '\n')
[[ ${#matches[@]} == 1 && "${matches[0]}" == i-* ]] || { echo 'Expected one running retained host' >&2; exit 1; }
umask 077
logs=$(mktemp -d "${TMPDIR:-/tmp}/secops-tunnels.XXXXXX")
pids=()
trap 'for pid in "${pids[@]}"; do kill -TERM "$pid" 2>/dev/null || true; done' EXIT
trap 'exit 130' INT TERM
for mapping in '3340:3340' '80:13080'; do
  remote=${mapping%:*}; local_port=${mapping#*:}
  aws ssm start-session --profile "$profile" --region "$region" --target "${matches[0]}" \
    --document-name AWS-StartPortForwardingSession \
    --parameters "{\"portNumber\":[\"$remote\"],\"localPortNumber\":[\"$local_port\"]}" \
    >"$logs/$local_port.log" 2>&1 &
  pids+=("$!")
done
for attempt in {1..20}; do
  if curl -fsS --max-time 2 http://localhost:3340/api/v1/get_source_health >/dev/null 2>&1 &&
     curl -fsS --max-time 2 http://localhost:13080/api/config >/dev/null 2>&1; then
    echo 'Operator: http://localhost:3340/'
    echo 'LibreChat: http://localhost:13080/'
    echo "Keep this terminal open. Private connection logs: $logs"
    wait -n "${pids[@]}"
    exit 1
  fi
  sleep 1
done
echo "Tunnel health failed; inspect private logs at $logs" >&2
exit 1
