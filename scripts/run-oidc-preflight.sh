#!/usr/bin/env bash
set -euo pipefail

GH_REPO="${GH_REPO:-amitkarpe/aws-secops}"
ROLE_NAME="${AWS_SECOPS_PREFLIGHT_ROLE_NAME:-github-actions-aws-secops-preflight}"
WORKFLOW="${AWS_SECOPS_PREFLIGHT_WORKFLOW:-aws-oidc-preflight.yml}"
REF="${AWS_SECOPS_PREFLIGHT_REF:-main}"

for cmd in aws gh grep; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "Missing required command: $cmd" >&2
    exit 1
  }
done

gh auth status >/dev/null

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
ROLE_ARN="$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)"

# Store only as GitHub repository variables. Never print either value.
gh variable set AWS_ALLOWED_ACCOUNT_ID --body "$ACCOUNT_ID" --repo "$GH_REPO"
gh variable set AWS_SECOPS_PREFLIGHT_ROLE_ARN --body "$ROLE_ARN" --repo "$GH_REPO"

# Verify variable names only.
VARIABLE_NAMES="$(gh variable list --repo "$GH_REPO" --json name --jq '.[].name')"
printf '%s\n' "$VARIABLE_NAMES" | grep -qx 'AWS_ALLOWED_ACCOUNT_ID'
printf '%s\n' "$VARIABLE_NAMES" | grep -qx 'AWS_SECOPS_PREFLIGHT_ROLE_ARN'

echo "Required repository variable names: PASS"

gh workflow run "$WORKFLOW" --ref "$REF" --repo "$GH_REPO"

# Allow GitHub a moment to register the dispatch, then select the newest matching run.
sleep 3
RUN_ID="$(gh run list \
  --repo "$GH_REPO" \
  --workflow "$WORKFLOW" \
  --event workflow_dispatch \
  --limit 1 \
  --json databaseId \
  --jq '.[0].databaseId')"

test -n "$RUN_ID"

gh run watch "$RUN_ID" --repo "$GH_REPO" --exit-status

gh run view "$RUN_ID" \
  --repo "$GH_REPO" \
  --json url,status,conclusion,workflowName \
  --jq '{url,status,conclusion,workflowName}'
