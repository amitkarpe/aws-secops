# Pilot v1 retained resources

Status: intentionally retained for repeatable demos

Private IDs, ARNs, endpoints, and the bucket name are recorded only in
`/home/user/.AGENTS-temp/aws-secops/pilot-v1/state.json`.

| Resource | Quantity | Purpose | Idle-cost behavior |
| --- | ---: | --- | --- |
| AgentCore Harness + managed Runtime | 1 | Nova 2 Lite specialist | Harness has no separate fee; Runtime is usage-based |
| AgentCore Gateway | 1 | exact MCP tool surface | indexed-tool charge; invocation charge only when used |
| AgentCore Policy engine | 1 | deterministic default-deny | authorization charge only when used |
| Gateway targets / exact tools | 3 | SG read, SG remediation, S3 read | indexed-tool charge |
| Lambda functions + IAM roles | 3 + 4 | exact providers/actions and Gateway execution | no Lambda or IAM idle compute charge |
| Dedicated unattached Security Group | 1 | reversible public-SSH finding | no Security Group hourly charge |
| Dedicated empty S3 bucket | 1 | five-control read-only baseline | storage and request charges only |
| CloudWatch log groups | 4 Pilot-owned | short operational evidence | Lambda 1-day; Runtime 7-day retention |

The reused research Gateway still has one earlier harmless target, so current
Gateway indexing covers four tools in total. It is not exposed by the Pilot
Harness allowlist.

## Retain-by-default decision

These resources are small, demo-owned, and avoid redeployment risk. Do not
delete them after a normal demo. Stop local UI processes and Runtime sessions;
retain control-plane resources until Amit explicitly retires the Pilot.

## Retirement checklist and command families

This is an inventory, not an automatic cleanup script. On explicit retirement:

1. verify `AWS_PROFILE=amit`, `ap-southeast-1`, resource tags, exact private
   state, zero Security Group attachments, and an empty bucket;
2. delete the three Pilot policies from the retained Policy engine;
3. delete the three Pilot Gateway targets;
4. delete the three Pilot Lambda functions, then their inline policies/roles;
5. delete the fixed demo Security Group;
6. empty all bucket versions/delete markers, then delete the demo bucket;
7. remove only Pilot log groups if evidence retention is no longer required;
8. delete the reused Harness/Gateway/Policy engine only if the Phase 0B
   research path is also retired.

Use `aws bedrock-agentcore-control delete-policy`, `delete-gateway-target`,
`delete-harness`, `delete-gateway`, and `delete-policy-engine`; `aws lambda
delete-function`; `aws iam delete-role-policy` and `delete-role`; `aws ec2
delete-security-group`; and version-aware `aws s3api` cleanup. Resolve every
identifier from the private state file and read it back immediately before its
individual deletion. Never use name globs or account-wide cleanup.
