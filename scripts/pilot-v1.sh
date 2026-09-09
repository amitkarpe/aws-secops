#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail

readonly AWS_PROFILE_NAME="${AWS_PROFILE:-amit}"
readonly AWS_REGION_NAME="${AWS_REGION:-ap-southeast-1}"
readonly PILOT_STATE_FILE="${PILOT_STATE_FILE:-/home/user/.AGENTS-temp/aws-secops/pilot-v1/state.json}"
readonly PILOT_PORT="${PILOT_PORT:-3340}"

fail() {
  echo "PILOT_V1_ERROR=$*" >&2
  exit 1
}

state_value() {
  jq -er --arg key "$1" '.[$key] | select(type == "string" and length > 0)' "$PILOT_STATE_FILE"
}

preflight() {
  [[ -r "$PILOT_STATE_FILE" ]] || fail "private state file is unavailable"
  [[ "$AWS_PROFILE_NAME" == "amit" ]] || fail "AWS_PROFILE must be amit"
  [[ "$AWS_REGION_NAME" == "ap-southeast-1" ]] || fail "AWS_REGION must be ap-southeast-1"
  local expected_account actual_account
  expected_account="$(state_value accountId)"
  actual_account="$(aws sts get-caller-identity --profile "$AWS_PROFILE_NAME" --query Account --output text)"
  [[ "$actual_account" == "$expected_account" ]] || fail "AWS identity does not match private Pilot state"
}

provider_status() {
  local group_id rule_count attachments
  group_id="$(state_value demoSecurityGroupId)"
  rule_count="$(aws ec2 describe-security-group-rules --profile "$AWS_PROFILE_NAME" --region "$AWS_REGION_NAME" --filters "Name=group-id,Values=$group_id" --query 'length(SecurityGroupRules[?IsEgress==`false` && IpProtocol==`tcp` && FromPort==`22` && ToPort==`22` && CidrIpv4==`0.0.0.0/0`])' --output text)"
  attachments="$(aws ec2 describe-network-interfaces --profile "$AWS_PROFILE_NAME" --region "$AWS_REGION_NAME" --filters "Name=group-id,Values=$group_id" --query 'length(NetworkInterfaces)' --output text)"
  [[ "$attachments" == "0" ]] || fail "dedicated demo Security Group is attached"
  if [[ "$rule_count" == "0" ]]; then
    echo "PILOT_SG_STATUS=COMPLIANT"
  elif [[ "$rule_count" == "1" ]]; then
    echo "PILOT_SG_STATUS=NON_COMPLIANT"
  else
    fail "dedicated demo Security Group has an unexpected SSH rule shape"
  fi
  echo "PILOT_SG_ATTACHMENTS=0"
}

rearm_sg() {
  local group_id status
  group_id="$(state_value demoSecurityGroupId)"
  status="$(provider_status | sed -n 's/^PILOT_SG_STATUS=//p')"
  if [[ "$status" == "COMPLIANT" ]]; then
    aws ec2 authorize-security-group-ingress \
      --profile "$AWS_PROFILE_NAME" \
      --region "$AWS_REGION_NAME" \
      --group-id "$group_id" \
      --protocol tcp \
      --port 22 \
      --cidr 0.0.0.0/0 >/dev/null
  fi
  [[ "$(provider_status | sed -n 's/^PILOT_SG_STATUS=//p')" == "NON_COMPLIANT" ]] || fail "demo rearm did not reach NON_COMPLIANT"
  echo "PILOT_V1_REARM=PASS"
  echo "PILOT_SG_STATUS=NON_COMPLIANT"
  echo "PILOT_SG_ATTACHMENTS=0"
}

serve() {
  export_pilot_config
  python3 -m pilot_v1.server --host 127.0.0.1 --port "$PILOT_PORT"
}

export_pilot_config() {
  export AWS_PROFILE="$AWS_PROFILE_NAME"
  export AWS_REGION="$AWS_REGION_NAME"
  export PILOT_HARNESS_ARN="$(state_value harnessArn)"
  export PILOT_GATEWAY_URL="$(state_value gatewayUrl)"
  export PILOT_SG_READ_TOOL="$(state_value readToolName)"
  export PILOT_SG_REMEDIATE_TOOL="$(state_value remediationToolName)"
  export PILOT_S3_READ_TOOL="$(state_value s3ToolName)"
}

smoke() {
  local result=0
  preflight
  rearm_sg >/dev/null
  export_pilot_config
  python3 -m pilot_v1.smoke || result=$?
  rearm_sg || result=$?
  if [[ "$result" == "0" ]]; then
    echo "PILOT_V1_1_SMOKE=PASS"
    echo "PLATFORM_PHASE1_SMOKE=PASS"
  else
    echo "PILOT_V1_1_SMOKE=BLOCKED" >&2
  fi
  return "$result"
}

usage() {
  echo "Usage: $0 {status|rearm-sg|serve|smoke|specialist-smoke}"
}

case "${1:-}" in
  status)
    preflight
    provider_status
    ;;
  rearm-sg)
    preflight
    rearm_sg
    ;;
  serve)
    preflight
    serve
    ;;
  smoke)
    smoke
    ;;
  specialist-smoke)
    preflight
    export_pilot_config
    python3 -m pilot_v1.smoke --specialists-only
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
