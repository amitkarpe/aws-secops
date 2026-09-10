#!/usr/bin/env bash
# Create only two new aliases; preserve legacy DNS; refuses conflicting records.
set -euo pipefail
: "${CHAT_HOST:?}" "${OPS_HOST:?}" "${LEGACY_HOST:?}" "${ZONE_ID:?}" "${PRIVATE_DIR:?}"
[[ "${AWS_PROFILE:-}" == amit ]] || { echo 'Use approved amit profile' >&2; exit 1; }
[[ "$CHAT_HOST" != "$OPS_HOST" && "$CHAT_HOST" != "$LEGACY_HOST" && "$OPS_HOST" != "$LEGACY_HOST" ]] || exit 1
umask 077
mkdir -p "$PRIVATE_DIR"
aws route53 list-resource-record-sets --profile amit --hosted-zone-id "$ZONE_ID" > "$PRIVATE_DIR/dns-current.json"
jq -e --arg name "$LEGACY_HOST." 'any(.ResourceRecordSets[]; .Name==$name and .Type=="A")' "$PRIVATE_DIR/dns-current.json" >/dev/null
jq --arg chat "$CHAT_HOST." --arg ops "$OPS_HOST." --arg legacy "$LEGACY_HOST." '
  .ResourceRecordSets as $records |
  {Comment:"aws-secops UI aliases; retained demo; review TTL 10-10-26; no automatic deletion",
   Changes:[[$chat,$ops][] | . as $name |
     [$records[]|select(.Name==$name)] as $existing |
     if ($existing|length)==0 then
       {Action:"CREATE",ResourceRecordSet:{Name:$name,Type:"CNAME",TTL:60,ResourceRecords:[{Value:$legacy}]}}
     elif ($existing|length)==1 and $existing[0].Type=="CNAME" and $existing[0].ResourceRecords==[{Value:$legacy}] then empty
     else error("Conflicting new hostname; no DNS overwrite authorized") end]} ' "$PRIVATE_DIR/dns-current.json" > "$PRIVATE_DIR/dns-change.json"
if [[ $(jq '.Changes|length' "$PRIVATE_DIR/dns-change.json") == 0 ]]; then
  echo 'DNS=UNCHANGED'; exit 0
fi
[[ "${1:-plan}" == apply ]] || { echo 'DNS_PLAN=READY (two aliases at most)'; exit 0; }
aws route53 change-resource-record-sets --profile amit --hosted-zone-id "$ZONE_ID" \
  --change-batch "file://$PRIVATE_DIR/dns-change.json" > "$PRIVATE_DIR/dns-result.json"
echo 'DNS_CHANGE=SUBMITTED (private result contains change ID)'
