# Specification

Status: approved — MVP-1 / Issue #1

## Problem

The R&D repo proved governance mechanics, but the clean product needs one real AgentCore-native security remediation path without historical POC plumbing.

## Scope

One Compliance Agent checks one real Security Group, asks for human approval when remediation is needed, invokes the actual bounded tool through Gateway Policy, and verifies provider state afterwards.

## MUST

- Run the Compliance Agent on AgentCore Harness in `ap-southeast-1`.
- Run the product workload in an approved Organizations member dev/sandbox account, not the management account.
- Put exact Security Group read/remediation tools behind MCP Gateway + AgentCore Policy.
- Prefer tiny Lambda MCP targets with narrow workload IAM.
- Use real provider reads and real provider resource identity in the private demo.
- Reject/no approval and Policy DENY must cause no remediation.
- Approved ALLOW removes only the intended unrestricted TCP/22 ingress rule.
- Re-read AWS and report COMPLIANT only when provider state proves it.
- Already-COMPLIANT is a no-op.
- Record a compact request -> human decision -> policy -> tool -> verification audit.

## MUST NOT

- Depend on Amit's SSO session at runtime.
- Deploy the product workload in the Organizations management account.
- Use company/production accounts.
- Expose a generic AWS CLI/API mutation tool or model-selected account/role/Region/action.
- Add Registry, StackSets, Security Hub, Inspector, Temporal Policy, WAF, EKS, Supervisor/A2A, or another control to MVP-1.
- Commit environment-specific account IDs/ARNs, credentials, tokens, private endpoints, or private evidence.

## Verification

One proportional live proof must demonstrate:

```text
real NON_COMPLIANT SG
-> human Approve
-> Gateway Policy ALLOW
-> exact remediation tool
-> AWS provider re-read
-> COMPLIANT
```

and one negative proof must show Reject or DENY -> zero remediation.

## Stop Gates

Stop for owner/controller review if implementation requires a different security model, the management/company/production account, broad AWS mutation capability, unrelated infrastructure, or secret/private-data exposure.
